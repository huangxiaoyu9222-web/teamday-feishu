import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
try:
    from teamday.web import make_server
except ImportError:
    make_server=None
from teamday.core import Service

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(make_server,'HTTP server not implemented')
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.s=Service(Path(self.tmp.name),True); self.addCleanup(self.s.close)
        self.http=make_server(self.s,0,Path(__file__).parents[1]/'static')
        threading.Thread(target=self.http.serve_forever,daemon=True).start()
        self.addCleanup(self.http.server_close); self.addCleanup(self.http.shutdown)
        self.base='http://127.0.0.1:'+str(self.http.server_port)
        self.csrf=self.get('/api/bootstrap')['csrf']
    def get(self,path):
        return json.load(urllib.request.urlopen(self.base+path))
    def post(self,path,p,csrf=True,origin=None):
        headers={'Content-Type':'application/json'}
        if csrf: headers['X-CSRF-Token']=self.csrf
        if origin: headers['Origin']=origin
        r=urllib.request.Request(self.base+path,data=json.dumps(p).encode(),headers=headers)
        return json.load(urllib.request.urlopen(r))
    def test_missing_csrf_and_foreign_origin_blocked(self):
        for kwargs in ({'csrf':False},{'origin':'https://evil.example'}):
            with self.assertRaises(urllib.error.HTTPError) as ctx: self.post('/api/brief',{'member':'jade'},**kwargs)
            self.assertEqual(ctx.exception.code,403)
    def test_http_execution_and_reload(self):
        state=self.get('/api/state?member=jade')
        r=self.post('/api/execute',{'member':'jade','brief_id':state['brief']['id'],'number':1})
        self.assertIn('body',r['artifact'])
        self.assertEqual(len(self.get('/api/state?member=jade')['artifacts']),1)
    def test_config_rejects_bad_timezone_as_client_error(self):
        c=self.get('/api/config'); c['schedule']['timezone']='Not/A/Zone'
        with self.assertRaises(urllib.error.HTTPError) as ctx: self.post('/api/config',c)
        self.assertEqual(ctx.exception.code,400)
    def test_static_path_and_error_does_not_leak(self):
        with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(self.base+'/static/../.env')

if __name__=='__main__': unittest.main()
