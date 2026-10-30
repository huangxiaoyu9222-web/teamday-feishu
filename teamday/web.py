"""Trusted local operator console; not an Internet-facing tenant server."""
import json
import mimetypes
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit, quote
from .core import DomainError


def make_server(service,port,static_root):
    csrf=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,fmt,*args): pass
        def response(self,status,body,ctype='application/json; charset=utf-8',filename=None):
            raw=json.dumps(body,ensure_ascii=False).encode() if isinstance(body,(dict,list)) else body
            if isinstance(raw,str): raw=raw.encode()
            self.send_response(status)
            self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if filename: self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+quote(filename))
            self.end_headers()
            try: self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError): pass
        def valid_origin(self):
            hosts={'127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)}
            host=self.headers.get('Host','')
            origin=self.headers.get('Origin')
            return host in hosts and (not origin or origin in {'http://'+h for h in hosts})
        def do_GET(self):
            if not self.valid_origin(): return self.response(403,{'error':'仅允许本机同源访问。'})
            try:
                url=urlsplit(self.path); q=parse_qs(url.query); member=q.get('member',[service.config['members'][0]['id']])[0]
                if url.path=='/api/bootstrap': return self.response(200,{'csrf':csrf})
                if url.path=='/api/state': return self.response(200,service.state(member,q.get('slot',['morning'])[0]))
                if url.path=='/api/config': return self.response(200,service.config)
                if url.path in ('/api/artifact','/download'):
                    a=service.artifact(member,q.get('id',[''])[0])
                    if url.path=='/download': return self.response(200,a['body'],'text/markdown; charset=utf-8',a['title']+'.md')
                    return self.response(200,{'artifact':a})
                if url.path=='/health': return self.response(200,{'ok':True,'mode':'demo' if service.demo else 'live'})
                relative='index.html' if url.path=='/' else url.path.removeprefix('/static/')
                if url.path!='/' and not url.path.startswith('/static/'): return self.response(404,{'error':'页面不存在。'})
                f=(static_root/relative).resolve()
                if f.parent!=static_root.resolve() or not f.is_file() or f.suffix not in ('.html','.js','.css','.svg','.png','.ico'):
                    return self.response(404,{'error':'文件不存在。'})
                return self.response(200,f.read_bytes(),(mimetypes.guess_type(str(f))[0] or 'text/plain')+'; charset=utf-8')
            except DomainError as e: self.response(400,{'error':str(e)})
            except Exception: self.response(500,{'error':'读取失败，请查看本地配置后重试。'})
        def do_POST(self):
            if not self.valid_origin() or not secrets.compare_digest(self.headers.get('X-CSRF-Token',''),csrf):
                return self.response(403,{'error':'请求校验失败，请刷新页面后重试。'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=150000: return self.response(413,{'error':'请求过大或为空。'})
                if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.response(415,{'error':'请提交 JSON。'})
                p=json.loads(self.rfile.read(size))
                if not isinstance(p,dict): raise DomainError('请求格式错误。')
                path=urlsplit(self.path).path
                if path=='/api/brief': r=service.brief(p.get('member'),p.get('slot','morning'),refresh=p.get('refresh',False))
                elif path=='/api/execute': r=service.execute(p.get('member'),p.get('brief_id'),p.get('number'))
                elif path=='/api/task': r=service.update_task(p.get('member'),p.get('id'),p.get('status'))
                elif path=='/api/notes/preview': r=service.preview_note(p)
                elif path=='/api/notes/confirm': r=service.confirm_note(p)
                elif path=='/api/config': r=service.save_config(p)
                elif path=='/api/news/refresh': r=service.refresh_news()
                elif path=='/api/push': r=service.push(p.get('member'),p.get('slot','morning'),explicit=True)
                else: return self.response(404,{'error':'接口不存在。'})
                self.response(200,r)
            except (DomainError,ValueError,TypeError) as e: self.response(400,{'error':str(e) if isinstance(e,DomainError) else '输入格式不正确。'})
            except Exception: self.response(500,{'error':'操作未完成，请检查配置后重试。没有将失败标记为成功。'})
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)
