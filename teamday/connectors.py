"""Bounded stdlib connectors; network calls are real and never silently simulated.

RSS is untrusted, not independently verified; unknown dates are retained as unknown.
Only public feed addresses are allowed, resolved addresses are pinned per connection,
and every redirect is validated. DNS/network failures become per-feed errors.
Model providers must support chat/completions. No streaming or automatic retries.
Feishu record creation has no idempotency guarantee and is never retried here.
"""
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

MAX_BODY = 2 * 1024 * 1024
TIMEOUT = 20
FEISHU_BASE = 'https://open.feishu.cn/open-apis'


class ConnectorError(Exception):
    pass


def load_env(path):
    try:
        with open(path, encoding='utf-8') as stream:
            for line in stream:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                if key.startswith('export '): key = key[7:].strip()
                if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                        value = value[1:-1]
                    os.environ.setdefault(key, value)
    except FileNotFoundError:
        pass


def _post(url, payload, token=None, timeout=TIMEOUT):
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    if token: headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method='POST')
    try:
        # POST redirects must not leak bearer credentials to another origin.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                raise ConnectorError('API redirect refused')
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(MAX_BODY + 1)
        if len(raw) > MAX_BODY: raise ConnectorError('API response too large')
        result = json.loads(raw)
        if not isinstance(result, dict): raise ConnectorError('Invalid API response')
        return result
    except ConnectorError:
        raise
    except urllib.error.HTTPError as exc:
        raise ConnectorError('API HTTP error %s' % exc.code) from None
    except Exception:
        raise ConnectorError('API request failed; check connection and configuration') from None


class ModelClient:
    @property
    def configured(self):
        return bool(os.environ.get('MODEL_API_KEY') and os.environ.get('MODEL_NAME'))

    def generate(self, system, user):
        if not self.configured: raise ConnectorError('Model credentials and model name required')
        base = os.environ.get('MODEL_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
        parts = urllib.parse.urlsplit(base)
        if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password:
            raise ConnectorError('Invalid model base URL')
        if parts.scheme == 'http':
            try:
                local = ipaddress.ip_address(parts.hostname).is_loopback
            except ValueError:
                local = parts.hostname.lower() == 'localhost'
            if not local:
                raise ConnectorError('Model credentials require HTTPS except for a loopback local model')
        try:
            timeout = max(10, min(180, int(os.environ.get('MODEL_TIMEOUT', '60'))))
        except (TypeError, ValueError):
            timeout = 60
        data = _post(base + '/chat/completions', {
            'model': os.environ['MODEL_NAME'],
            'messages': [{'role':'system','content':system}, {'role':'user','content':user}],
        }, os.environ['MODEL_API_KEY'], timeout=timeout)
        try:
            content = data['choices'][0]['message']['content']
            if not isinstance(content, str) or not content.strip(): raise ValueError()
            return content
        except (KeyError, IndexError, TypeError, ValueError):
            raise ConnectorError('Model returned no usable text') from None


class FeishuClient:
    @property
    def configured(self):
        return bool(os.environ.get('FEISHU_APP_ID') and os.environ.get('FEISHU_APP_SECRET'))

    @property
    def bitable_configured(self):
        return bool(self.configured and os.environ.get('FEISHU_BITABLE_APP_TOKEN') and os.environ.get('FEISHU_BITABLE_TABLE_ID'))

    def _check(self, data):
        if data.get('code') != 0: raise ConnectorError('Feishu rejected request (check app permissions and configuration)')
        return data

    def _token(self):
        if not self.configured: raise ConnectorError('Feishu app credentials required')
        data = self._check(_post(FEISHU_BASE + '/auth/v3/tenant_access_token/internal', {
            'app_id': os.environ['FEISHU_APP_ID'], 'app_secret':os.environ['FEISHU_APP_SECRET']}))
        token = data.get('tenant_access_token')
        if not isinstance(token, str) or not token: raise ConnectorError('Feishu token missing')
        return token

    def send_text(self, open_id, text, dedupe_key):
        if not open_id or not dedupe_key: raise ConnectorError('Recipient and deduplication key required')
        data = self._check(_post(FEISHU_BASE + '/im/v1/messages?receive_id_type=open_id', {
            'receive_id':open_id, 'msg_type':'text', 'content':json.dumps({'text':text}, ensure_ascii=False),
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL, str(dedupe_key)))}, self._token()))
        message_id = data.get('data', {}).get('message_id')
        if not message_id: raise ConnectorError('Feishu message result uncertain: message ID missing')
        return message_id

    def write_record(self, fields):
        if not self.bitable_configured: raise ConnectorError('Feishu Bitable configuration required')
        app = urllib.parse.quote(os.environ['FEISHU_BITABLE_APP_TOKEN'], safe='')
        table = urllib.parse.quote(os.environ['FEISHU_BITABLE_TABLE_ID'], safe='')
        data = self._check(_post(FEISHU_BASE + '/bitable/v1/apps/%s/tables/%s/records' % (app, table),
                                 {'fields':fields}, self._token()))
        record_id = data.get('data', {}).get('record', {}).get('record_id')
        if not record_id: raise ConnectorError('Bitable result uncertain; do not blindly retry')
        return record_id


def validate_feed_url(url):
    try:
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ('https','http') or not parts.hostname or parts.username is not None or parts.password is not None:
            raise ValueError()
        if parts.port not in (None, 80, 443): raise ValueError()
        host = parts.hostname.rstrip('.').lower()
        if host == 'localhost' or host.endswith('.localhost') or '%' in host: raise ValueError()
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            literal = None
        if literal is not None and not literal.is_global: raise ValueError()
        port = parts.port or (443 if parts.scheme == 'https' else 80)
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        if not addresses: raise ValueError()
        for entry in addresses:
            address = ipaddress.ip_address(entry[4][0])
            if not address.is_global: raise ValueError()
        return parts, addresses[0][4][0], port
    except Exception:
        raise ConnectorError('Feed URL must resolve only to public HTTP(S) addresses on port 80/443') from None


def _fetch_feed(url):
    for _ in range(6):
        parts, address, port = validate_feed_url(url)
        conn = http.client.HTTPConnection(parts.hostname, port, timeout=TIMEOUT)
        try:
            conn.sock = socket.create_connection((address, port), timeout=TIMEOUT)
            if parts.scheme == 'https':
                conn.sock = ssl.create_default_context().wrap_socket(conn.sock, server_hostname=parts.hostname)
            path = urllib.parse.urlunsplit(('', '', parts.path or '/', parts.query, ''))
            conn.request('GET', path, headers={'User-Agent':'TeamDay/0.1 RSS', 'Accept':'application/rss+xml, application/atom+xml, application/xml'})
            response = conn.getresponse()
            if response.status in (301,302,303,307,308):
                location = response.getheader('Location')
                if not location: raise ConnectorError('Feed redirect missing destination')
                url = urllib.parse.urljoin(url, location)
                continue
            if response.status != 200: raise ConnectorError('Feed HTTP error %s' % response.status)
            body = response.read(MAX_BODY + 1)
            if len(body) > MAX_BODY: raise ConnectorError('Feed response too large')
            return body
        finally:
            conn.close()
    raise ConnectorError('Too many feed redirects')


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data): self.parts.append(data)


def _plain(value):
    parser = _Text()
    parser.feed(value or '')
    return ' '.join(' '.join(parser.parts).split())[:4000]


def _date(value):
    if not value: return None
    try:
        try: result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError: result = parsedate_to_datetime(value)
        if result.tzinfo is None: result = result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError): return None


def _canonical_url(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme.lower() not in ('http', 'https') or not parts.hostname:
        return ''
    host = parts.hostname.lower().rstrip('.')
    if ':' in host: host = '[' + host + ']'
    port = parts.port
    if port and (parts.scheme.lower(), port) not in (('https', 443), ('http', 80)):
        host += ':' + str(port)
    return urllib.parse.urlunsplit((parts.scheme.lower(), host, parts.path or '/', parts.query, ''))


def fetch_feeds(feeds, limit=20):
    items, errors = [], []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=14)
    for feed in feeds:
        name = str(feed.get('name') or 'RSS')[:100]
        try:
            raw = _fetch_feed(feed.get('url', ''))
            if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper(): raise ConnectorError('Feed DTD/entities rejected')
            root = ET.fromstring(raw)
            for entry in root.iter():
                if entry.tag.split('}')[-1] not in ('item','entry'): continue
                fields = {}
                for child in entry:
                    tag = child.tag.split('}')[-1]
                    if tag == 'link' and child.get('href'):
                        if child.get('rel', 'alternate') == 'alternate': fields['link'] = child.get('href')
                    else: fields.setdefault(tag, ''.join(child.itertext()))
                date = _date(fields.get('pubDate') or fields.get('published') or fields.get('updated') or fields.get('date'))
                if date and (date < cutoff or date > now + timedelta(hours=24)): continue
                link = _canonical_url(urllib.parse.urljoin(feed.get('url',''), fields['link'])) if fields.get('link') else ''
                title = _plain(fields.get('title',''))[:300]
                key = hashlib.sha256((link or (name + '\n' + title)).encode()).hexdigest()[:24]
                items.append({'id':key,'title':title,'url':link,'source':name,
                              'published_at':date.isoformat() if date else '',
                              'summary':_plain(fields.get('description') or fields.get('summary') or fields.get('content','')),
                              'verification':'来源待复核' if date else '发布时间未知 · 来源待复核'})
        except Exception:
            errors.append(name + ': 获取或解析失败，请检查公开来源地址与网络')
    items.sort(key=lambda item: item['published_at'], reverse=True)
    unique, seen = [], set()
    for item in items:
        if item['id'] not in seen:
            unique.append(item)
            seen.add(item['id'])
    return {'items':unique[:max(0, min(int(limit), 200))], 'errors':errors}
