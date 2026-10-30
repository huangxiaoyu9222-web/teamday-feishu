#!/usr/bin/env python3
"""Run: python3 app.py [--live] [--feishu-listen] [--port 8765] [--open]."""
import argparse
import fcntl
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
from teamday.connectors import load_env
from teamday.core import Service
from teamday.web import make_server


def main():
    parser=argparse.ArgumentParser(description='TeamDay · 团队日常助手')
    parser.add_argument('--live',action='store_true',help='使用独立真实数据库和配置；不含演示资料')
    parser.add_argument('--feishu-listen',action='store_true',help='启用飞书长连接，需安装 requirements-feishu.txt')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--open',action='store_true',help='打开浏览器')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    load_env(root/'.env')
    if args.feishu_listen and not all(os.environ.get(k) for k in ('FEISHU_APP_ID','FEISHU_APP_SECRET')):
        print('缺少飞书应用凭证。请在 .env 填写 FEISHU_APP_ID / FEISHU_APP_SECRET，按 docs/FEISHU.md 完成授权后重启。')
        print('Missing Feishu credentials. Complete .env and follow docs/FEISHU.en.md, then restart.')
        return 1
    (root/'data').mkdir(exist_ok=True)
    lock=open(root/'data'/('live.lock' if args.live else 'demo.lock'),'a')
    try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        print('同一模式的服务已运行，请打开已有页面或先停止旧进程。'); return 1
    if args.feishu_listen and not args.live:
        print('飞书监听只能在 --live 模式启用。'); return 1
    service=Service(root,demo=not args.live)
    try: server=make_server(service,args.port,root/'static')
    except OSError:
        print('端口已占用，可尝试 --port 8766。'); service.close(); return 1
    stop=threading.Event()
    def scheduler():
        while not stop.is_set():
            try: service.tick()
            except Exception: print('定时任务本轮未完成；请检查配置，下一轮将继续检查。')
            stop.wait(30)
    threading.Thread(target=scheduler,daemon=True).start()
    url='http://127.0.0.1:'+str(server.server_port)
    print('TeamDay 已启动：'+url,flush=True)
    print('模式：'+('真实连接（需配置凭证）' if args.live else '演示（不向外发送）'),flush=True)
    print('按 Ctrl+C 停止。自动推送只在服务持续运行时生效。',flush=True)
    if args.open: webbrowser.open(url)
    try:
        if args.feishu_listen:
            threading.Thread(target=server.serve_forever,daemon=True).start()
            from teamday.listener import listen
            listen(service)
        else: server.serve_forever()
    except KeyboardInterrupt: pass
    except Exception as e:
        print('监听未能启动，请检查依赖、应用凭证与飞书长连接设置。',flush=True)
        return 1
    finally:
        stop.set(); server.server_close()
    return 0

if __name__=='__main__': sys.exit(main())
