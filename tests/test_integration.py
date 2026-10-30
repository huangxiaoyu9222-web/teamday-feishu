"""Exercise real HTTP serialization against a local protocol simulator, not a live tenant."""
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from teamday.core import Service


class WorkflowIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.requests=[]
        requests=self.requests
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                p=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append((self.path,p))
                if self.path=='/v1/chat/completions':
                    user=json.loads(p['messages'][1]['content'])
                    if 'raw' in user:
                        answer=json.dumps({'corrected':'赵岚：仅验证，不承诺采购。','summary':'仅验证；采购人待确认。','warnings':['采购决策人未确认。']},ensure_ascii=False)
                    else:
                        answer='# 待审草稿\n仅验证；采购人待确认。\n来源：'+user['context']['notes'][0]['id']
                    result={'choices':[{'message':{'content':answer}}]}
                elif '/auth/' in self.path: result={'code':0,'tenant_access_token':'simulated-token'}
                elif '/im/v1/messages' in self.path: result={'code':0,'data':{'message_id':'simulated-message'}}
                elif '/bitable/' in self.path: result={'code':0,'data':{'record':{'record_id':'simulated-record'}}}
                else: self.send_error(404);return
                body=json.dumps(result).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        self.http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=self.http.serve_forever,daemon=True).start()
        self.addCleanup(self.http.server_close);self.addCleanup(self.http.shutdown)
        base='http://127.0.0.1:'+str(self.http.server_port)
        env=patch.dict(os.environ,{'MODEL_API_KEY':'simulated-key','MODEL_NAME':'simulated-model','MODEL_BASE_URL':base+'/v1','FEISHU_APP_ID':'simulated-app','FEISHU_APP_SECRET':'simulated-secret','FEISHU_BITABLE_APP_TOKEN':'simulated-bitable','FEISHU_BITABLE_TABLE_ID':'simulated-table'},clear=True)
        env.start();self.addCleanup(env.stop)
        target=patch('teamday.connectors.FEISHU_BASE',base);target.start();self.addCleanup(target.stop)
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.s=Service(Path(tmp.name),False);self.addCleanup(self.s.close)
        self.s.config['members'][0]['open_id']='ou_simulated'
    def test_note_to_delivery_numeric_reply_and_table(self):
        n=self.s.preview_note(dict(member='jade',org='合成工厂',project='模拟验收',people='赵岚｜使用方；采购人待确认',raw='赵蓝：仅验证，不承诺采购。',visibility='team'))
        self.assertIn('赵岚',n['corrected'])
        self.assertEqual(self.s.knowledge('jade'),[])
        self.s.confirm_note(dict(member='jade',id=n['id'],corrected=n['corrected'],summary=n['summary'],todos=['确认数据授权']))
        delivery=self.s.push('jade')
        self.assertEqual(delivery['status'],'sent')
        reply=self.s.receive('ou_simulated','inbound-1','1')
        self.assertIn(n['id'],reply)
        self.assertIn('simulated-record',reply)
        count=len(self.requests)
        self.assertEqual(self.s.receive('ou_simulated','inbound-1','1'),reply)
        self.assertEqual(len(self.requests),count)
        self.assertEqual(len(self.s.all('artifact')),1)
        sent=next(p for path,p in self.requests if '/im/v1/messages' in path)
        self.assertEqual(sent['receive_id'],'ou_simulated')
        self.assertIn('确认数据授权',json.loads(sent['content'])['text'])
        table=next(p for path,p in self.requests if '/bitable/' in path)
        action_payload=next(json.loads(p['messages'][1]['content']) for path,p in self.requests if path=='/v1/chat/completions' and 'action' in json.loads(p['messages'][1]['content']))
        self.assertNotIn('raw',action_payload['context']['notes'][0])
        self.assertIn('赵岚',action_payload['context']['notes'][0]['corrected'])
        self.assertEqual(table['fields']['状态'],'初稿待审')
        self.assertIn('采购人待确认',table['fields']['内容'])
