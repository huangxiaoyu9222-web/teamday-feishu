import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
try:
    from teamday.core import Service, DomainError
except ImportError:
    Service = None
    DomainError = ValueError

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.assertIsNotNone(Service, 'domain service has not been implemented')
        self.s = Service(Path(self.tmp.name), demo=True)
        self.addCleanup(self.s.close)

    def test_roles_have_different_actions(self):
        a=self.s.brief('jade'); b=self.s.brief('lin')
        self.assertNotEqual(a['actions'][0]['title'],b['actions'][0]['title'])

    def test_repeat_action_returns_same_artifact(self):
        b=self.s.brief('jade')
        a=self.s.execute('jade',b['id'],1)
        again=self.s.execute('jade',b['id'],1)
        self.assertEqual(a['artifact']['id'],again['artifact']['id'])
        self.assertEqual(len(self.s.state('jade')['artifacts']),1)

    def test_another_member_cannot_execute_or_read_artifact(self):
        b=self.s.brief('jade'); a=self.s.execute('jade',b['id'],1)
        with self.assertRaises(DomainError): self.s.execute('lin',b['id'],1)
        with self.assertRaises(DomainError): self.s.artifact('lin',a['artifact']['id'])

    def test_draft_not_used_until_confirmed_and_original_preserved(self):
        note=self.s.preview_note(dict(member='jade',org='某工厂',project='测试',people='王建国',raw='王建功说：先验证，不承诺部署。',visibility='private'))
        self.assertNotIn(note['id'],[n['id'] for n in self.s.knowledge('jade')])
        self.s.confirm_note(dict(member='jade',id=note['id'],corrected='王建国说：先验证，不承诺部署。',summary='仅验证',todos=['确认数据范围']))
        n=[n for n in self.s.knowledge('jade') if n['id']==note['id']][0]
        self.assertIn('王建功',n['raw'])
        self.assertIn('王建国',n['corrected'])
        self.assertNotIn(note['id'],[n['id'] for n in self.s.knowledge('lin')])

    def test_repeated_note_does_not_duplicate(self):
        p=dict(member='jade',org='某工厂',project='测试',people='王工',raw='待确认',visibility='team')
        self.assertEqual(self.s.preview_note(p)['id'],self.s.preview_note(p)['id'])

    def test_confirm_is_idempotent_and_owner_only(self):
        n=self.s.preview_note(dict(member='jade',org='某工厂',project='测试',people='王工',raw='待确认',visibility='team'))
        p=dict(member='jade',id=n['id'],corrected='待确认',summary='待确认',todos=['核对'])
        with self.assertRaises(DomainError): self.s.confirm_note(dict(p,member='lin'))
        self.s.confirm_note(p); self.s.confirm_note(p)
        self.assertEqual(sum(t['source']==n['id'] for t in self.s.state('jade')['tasks']),1)

    def test_task_owner_and_state_validation(self):
        t=self.s.state('jade')['tasks'][0]
        with self.assertRaises(DomainError): self.s.update_task('lin',t['id'],'done')
        with self.assertRaises(DomainError): self.s.update_task('jade',t['id'],'invented')
        self.assertEqual(self.s.update_task('jade',t['id'],'done')['status'],'done')

    def test_snapshot_stable_and_live_is_empty(self):
        self.assertEqual(self.s.brief('jade')['id'],self.s.brief('jade')['id'])
        live=Service(Path(self.tmp.name),demo=False)
        try:
            self.assertEqual(live.knowledge('jade'),[])
            self.assertEqual(live.state('jade')['tasks'],[])
        finally: live.close()

    def test_demo_never_sends(self):
        with self.assertRaises(DomainError): self.s.push('jade','morning')

    def test_config_rejects_bad_schedule_and_duplicate_member(self):
        c=self.s.config.copy(); c['schedule']=dict(c['schedule'],morning='26:00')
        with self.assertRaises(DomainError): self.s.save_config(c)
        c=self.s.config.copy(); c['members']=c['members']+[c['members'][0]]
        with self.assertRaises(DomainError): self.s.save_config(c)

    def test_failed_generation_does_not_claim_done(self):
        class Bad:
            configured=True
            def generate(self,*a): raise RuntimeError('upstream failed')
        self.s.demo=False; self.s.model=Bad()
        b=self.s.brief('jade')
        with self.assertRaises(DomainError): self.s.execute('jade',b['id'],1)
        self.assertEqual(self.s.brief('jade')['actions'][0]['status'],'failed')
        self.assertEqual(self.s.state('jade')['artifacts'],[])

if __name__=='__main__': unittest.main()

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.s=Service(Path(self.tmp.name),False); self.addCleanup(self.s.close)
        class FakeFeishu:
            configured=True; bitable_configured=False
            def __init__(self): self.calls=[]
            def send_text(self,recipient,text,k): self.calls.append((recipient,text,k)); return 'message-'+k
        self.f=FakeFeishu(); self.s.feishu=self.f
        self.s.config['members'][0]['open_id']='ou_test'
        self.s.config['schedule']['enabled']=True
    def test_schedule_once_and_no_late_replay(self):
        d=datetime(2026,10,30,8,10,tzinfo=ZoneInfo('Asia/Shanghai'))
        self.s.tick(d); self.s.tick(d)
        self.assertEqual(len(self.f.calls),1)
        self.s.tick(d.replace(hour=10))
        self.assertEqual(len(self.f.calls),1)
    def test_weekend_and_unbound_member_not_sent(self):
        self.s.tick(datetime(2026,10,31,8,10,tzinfo=ZoneInfo('Asia/Shanghai')))
        self.assertEqual(self.f.calls,[])
    def test_latest_pushed_card_overrides_older_requested_card(self):
        self.s.seed()
        self.s.receive('ou_test','msg1','早报')
        morning=self.s.get('pointer','jade')['brief_id']
        noon=self.s.push('jade','midday')
        self.s.receive('ou_test','msg2','1')
        # noon has no signals/actions; should not execute morning action nor silently reference morning
        self.assertIn('编号不存在',self.s.get('inbound','msg2')['reply'])
        self.assertNotEqual(morning,noon['brief_id'])
    def test_refresh_rejects_old_action(self):
        b=self.s.brief('jade'); new=self.s.brief('jade',refresh=True)
        self.assertNotEqual(b['id'],new['id'])
        with self.assertRaises(DomainError): self.s.execute('jade',b['id'],1)
    def test_invalid_model_suggestion_preserves_raw(self):
        class BadModel:
            configured=True
            def generate(self,*args): return 'not json'
        self.s.model=BadModel()
        n=self.s.preview_note(dict(member='jade',org='工厂',project='项目',people='王工',raw='原始文本',visibility='private'))
        self.assertEqual(n['corrected'],'原始文本')
        self.assertTrue(n.get('warnings'))

class DeliveryRevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.s=Service(Path(self.tmp.name),False); self.addCleanup(self.s.close)
        self.s.seed()
        self.s.config['members'][0]['open_id']='ou_test'
        class Fake:
            configured=True; bitable_configured=True
            def __init__(self): self.sent=[];self.written=[]
            def send_text(self,o,t,k): self.sent.append((o,t,k));return 'msg-'+str(len(self.sent))
            def write_record(self,f): self.written.append(f); return 'rec1'
        self.f=Fake();self.s.feishu=self.f
    def test_refresh_then_explicit_send_uses_new_card_once(self):
        old=self.s.push('jade','morning')
        newbrief=self.s.brief('jade',refresh=True)
        new=self.s.push('jade','morning',explicit=True)
        self.assertNotEqual(old['brief_id'],new['brief_id'])
        self.assertEqual(new['brief_id'],newbrief['id'])
        self.s.push('jade','morning',explicit=True)
        self.assertEqual(len(self.f.sent),2)
        self.assertEqual(self.s.push('jade','morning')['brief_id'],new['brief_id'])
    def test_private_note_artifact_not_written_to_shared_table(self):
        n=self.s.preview_note(dict(member='jade',org='私密工厂',project='私密项目',people='王工',raw='私密内容',visibility='private'))
        self.s.confirm_note(dict(member='jade',id=n['id'],corrected='私密内容',summary='这是私密上下文',todos=[]))
        b=self.s.brief('jade',refresh=True)
        class Good:
            configured=True
            def generate(self,*args): return '# 草稿\n这是私密上下文'
        self.s.model=Good()
        r=self.s.execute('jade',b['id'],1)
        self.assertEqual(self.f.written,[])
        self.assertIn('个人',r['writeback'])

class ReleaseAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.s=Service(Path(self.tmp.name),False); self.addCleanup(self.s.close)
    def test_schedule_refreshes_previously_opened_brief(self):
        self.s.config['schedule']['enabled']=True
        self.s.config['members'][0]['open_id']='ou_test'
        now=self.s.now().replace(hour=8,minute=10,second=0)
        self.s.config['schedule']['weekdays_only']=False
        old=self.s.brief('jade',now=now)
        item={'id':'new','title':'工业 Agent 新资料','summary':'现场调研','url':'https://example.com/new','verification':'待核验'}
        def refresh(): self.s.put('news',item); return {'items':[item],'errors':[]}
        self.s.refresh_news=refresh
        class Fake:
            configured=True
            def send_text(self,*args): return 'msg'
        self.s.feishu=Fake()
        result=self.s.tick(now)
        sent=self.s.get('brief',result[0]['brief_id'])
        self.assertNotEqual(sent['id'],old['id'])
        self.assertEqual(sent['signals'][0]['id'],'new')
    def test_private_task_excluded_from_shared_writeback_even_outside_note_window(self):
        self.s.seed()
        n=self.s.preview_note(dict(member='jade',org='私密厂',project='旧私密项目',people='甲',raw='私密',visibility='private'))
        self.s.confirm_note(dict(member='jade',id=n['id'],corrected='私密',summary='私密',todos=['私密待办']))
        for i in range(6):
            n2=self.s.preview_note(dict(member='jade',org='团队厂',project=str(i),people='乙',raw=str(i),visibility='team'))
            self.s.confirm_note(dict(member='jade',id=n2['id'],corrected=str(i),summary=str(i),todos=[]))
        class Model:
            configured=True
            def generate(self,*args): return '包含私密待办的草稿'
        class Fake:
            configured=True; bitable_configured=True
            def __init__(self): self.writes=[]
            def write_record(self,fields): self.writes.append(fields);return 'record'
        self.s.model=Model(); f=Fake(); self.s.feishu=f
        b=self.s.brief('jade'); self.s.execute('jade',b['id'],1)
        self.assertEqual(f.writes,[])
    def test_empty_brief_has_no_nonexistent_execution_instruction(self):
        b=self.s.brief('jade')
        text=self.s.brief_text(b)
        self.assertNotIn(b['id'],text)
        self.assertIn('暂无可生成的行动',text)
