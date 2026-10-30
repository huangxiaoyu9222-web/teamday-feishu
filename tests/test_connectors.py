import io
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from teamday.connectors import (ConnectorError, ModelClient, FeishuClient,
                                fetch_feeds, validate_feed_url)


class Reply(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class ConnectorsTest(unittest.TestCase):
    def test_private_addresses_rejected(self):
        for url in ['http://localhost/x', 'http://127.0.0.1/x', 'http://169.254.169.254/',
                    'http://[::1]/', 'file:///etc/passwd', 'https://u:p@example.com',
                    'http://example.com:8080']:
            with self.subTest(url=url), self.assertRaises(ConnectorError):
                validate_feed_url(url)
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('10.1.2.3', 80))]):
            with self.assertRaises(ConnectorError): validate_feed_url('https://example.com')

    def test_rss_and_atom(self):
        date = datetime.now(timezone.utc).isoformat()
        rss = '<rss><channel><item><title>RSS</title><link>https://example.com/a</link><description>&lt;b&gt;hello&lt;/b&gt;</description></item></channel></rss>'
        atom = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom</title><link href="https://example.com/b"/><updated>%s</updated><summary>world</summary></entry></feed>' % date
        with patch('teamday.connectors._fetch_feed', side_effect=[rss.encode(), atom.encode()]):
            result = fetch_feeds([{'name':'A','url':'https://example.com'}, {'name':'B','url':'https://example.org'}])
        self.assertEqual(len(result['items']), 2)
        self.assertEqual(result['items'][1]['summary'], 'hello')
        self.assertEqual(result['items'][1]['published_at'], '')
        self.assertEqual(result['items'][0]['verification'], '来源待复核')

    def test_feishu_code_failure(self):
        with patch.dict('os.environ', {'FEISHU_APP_ID':'app','FEISHU_APP_SECRET':'secret'}, clear=True):
            with patch('urllib.request.OpenerDirector.open', return_value=Reply(b'{"code":999,"msg":"secret"}')):
                with self.assertRaises(ConnectorError) as ctx:
                    FeishuClient().send_text('ou_x','hello','once')
                self.assertNotIn('secret', str(ctx.exception))

    def test_model_failure_and_unconfigured(self):
        with patch.dict('os.environ', {}, clear=True):
            self.assertFalse(ModelClient().configured)
            with self.assertRaises(ConnectorError): ModelClient().generate('s','u')
        with patch.dict('os.environ', {'MODEL_API_KEY':'sensitive','MODEL_NAME':'m'}, clear=True):
            with patch('urllib.request.OpenerDirector.open', side_effect=OSError('sensitive')):
                with self.assertRaises(ConnectorError) as ctx: ModelClient().generate('s','u')
                self.assertNotIn('sensitive', str(ctx.exception))

    def test_send_uuid_stable_and_bitable_no_retry(self):
        env = {'FEISHU_APP_ID':'app','FEISHU_APP_SECRET':'secret',
               'FEISHU_BITABLE_APP_TOKEN':'base','FEISHU_BITABLE_TABLE_ID':'table'}
        with patch.dict('os.environ', env, clear=True):
            responses = [{'code':0,'tenant_access_token':'t'},
                         {'code':0,'data':{'message_id':'m'}}] * 2
            with patch('teamday.connectors._post', side_effect=responses) as post:
                client = FeishuClient()
                self.assertEqual(client.send_text('ou_x','hi','same'), 'm')
                client.send_text('ou_x','hi','same')
                first = post.call_args_list[1].args[1]['uuid']
                self.assertEqual(first, post.call_args_list[3].args[1]['uuid'])
                self.assertLessEqual(len(first), 50)
            with patch('teamday.connectors._post', side_effect=[
                {'code':0,'tenant_access_token':'t'}, ConnectorError('uncertain')]) as post:
                with self.assertRaises(ConnectorError): client.write_record({'Name':'x'})
                self.assertEqual(post.call_count, 2)

    def test_old_entries_and_feed_failure(self):
        rss = b'<rss><channel><item><title>Old</title><pubDate>Mon, 01 Jan 2001 00:00:00 GMT</pubDate></item></channel></rss>'
        with patch('teamday.connectors._fetch_feed', side_effect=[rss, OSError('internal')]):
            result = fetch_feeds([{'name':'old','url':'https://example.com'},
                                  {'name':'bad','url':'https://example.org'}])
        self.assertEqual(result['items'], [])
        self.assertEqual(len(result['errors']), 1)
        self.assertNotIn('internal', result['errors'][0])

    def test_redirect_destination_revalidated(self):
        response = unittest.mock.Mock(status=302)
        response.getheader.return_value = 'http://127.0.0.1/secret'
        conn = unittest.mock.Mock()
        conn.getresponse.return_value = response
        with patch('socket.getaddrinfo', return_value=[(2,1,6,'',('93.184.216.34',80))]):
            with patch('socket.create_connection'), patch('http.client.HTTPConnection', return_value=conn):
                # DNS mock returns public for all hosts; literal IP must still be rejected.
                from teamday.connectors import _fetch_feed
                with self.assertRaisesRegex(ConnectorError, 'public HTTP'): _fetch_feed('http://example.com/')
                self.assertEqual(conn.request.call_count, 1)

    def test_order_dedupe_future_and_unknown(self):
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        def item(title, link, date):
            return '<item><title>%s</title><link>%s</link><pubDate>%s</pubDate></item>' % (title,link,date)
        first = '<rss><channel>' + item('old headline','https://EXAMPLE.com:443/a#one',(now-timedelta(days=2)).isoformat()) + item('unknown','https://example.com/u','') + '</channel></rss>'
        second = '<rss><channel>' + item('new headline','https://example.com/a#two',now.isoformat()) + item('future','https://example.com/f',(now+timedelta(days=2)).isoformat()) + item('recent','https://example.com/r',(now-timedelta(hours=1)).isoformat()) + '</channel></rss>'
        with patch('teamday.connectors._fetch_feed', side_effect=[first.encode(),second.encode()]):
            result = fetch_feeds([{'name':'a','url':'https://example.com'}, {'name':'b','url':'https://example.org'}])
        self.assertEqual([x['title'] for x in result['items']], ['new headline','recent','unknown'])
        self.assertEqual(result['items'][-1]['verification'], '发布时间未知 · 来源待复核')

    def test_model_transport_and_timeout(self):
        env = {'MODEL_API_KEY':'sensitive','MODEL_NAME':'m', 'MODEL_BASE_URL':'http://example.com/v1'}
        with patch.dict('os.environ', env, clear=True), patch('teamday.connectors._post') as post:
            with self.assertRaises(ConnectorError): ModelClient().generate('s','u')
            post.assert_not_called()
        for setting, expected in [('1',10), ('300',180), ('bad',60), ('80',80)]:
            env.update(MODEL_BASE_URL='http://127.0.0.1:11434/v1', MODEL_TIMEOUT=setting)
            with patch.dict('os.environ', env, clear=True), patch('teamday.connectors._post', return_value={'choices':[{'message':{'content':'ok'}}]}) as post:
                self.assertEqual(ModelClient().generate('s','u'), 'ok')
                self.assertEqual(post.call_args.kwargs['timeout'], expected)


if __name__ == '__main__': unittest.main()
