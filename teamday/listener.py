"""Optional official Feishu SDK WebSocket transport. Only private text messages are accepted."""
import json
import os
from concurrent.futures import ThreadPoolExecutor


def listen(service):
    import lark_oapi as lark
    if not service.feishu.configured: raise RuntimeError('Missing Feishu credentials')
    pool=ThreadPoolExecutor(max_workers=2)
    def process(open_id,message_id,text):
        try:
            reply=service.receive(open_id,message_id,text)
            service.feishu.send_text(open_id,reply,'reply-'+message_id)
        except Exception:
            print('一条飞书消息处理或回复未完成；可在本地成果页查看。')
    def handler(event):
        msg=event.event.message
        if msg.chat_type!='p2p' or msg.message_type!='text': return
        open_id=event.event.sender.sender_id.open_id
        # Ignore unbound users before any output or model call.
        if not any(m.get('open_id')==open_id and open_id for m in service.config['members']): return
        try:
            text=json.loads(msg.content).get('text','')
            if not isinstance(text,str) or len(text)>500: return
        except (ValueError,TypeError): return
        pool.submit(process,open_id,msg.message_id,text)
    dispatcher=lark.EventDispatcherHandler.builder('','').register_p2_im_message_receive_v1(handler).build()
    client=lark.ws.Client(os.environ['FEISHU_APP_ID'],os.environ['FEISHU_APP_SECRET'],event_handler=dispatcher,log_level=lark.LogLevel.ERROR)
    service.listener=True
    try: client.start()
    finally: service.listener=False; pool.shutdown(wait=False)
