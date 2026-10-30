#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo '请先安装 Python 3.9+ / Install Python 3.9+ first.'
  read '?按回车关闭 / Press Return to close.'
  exit 1
fi
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo '已生成 .env。请填写凭证，再次启动。接入说明：docs/FEISHU.md / docs/FEISHU.en.md'
  echo 'Created .env. Enter your credentials locally, then launch again.'
  open -e .env
  read '?按回车关闭 / Press Return to close.'
  exit 0
fi
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv || { read '?创建环境失败 / Environment creation failed. Press Return.'; exit 1; }
fi
if ! .venv/bin/python -c 'import lark_oapi' >/dev/null 2>&1; then
  echo '首次安装飞书 SDK / Installing the official Feishu SDK…'
  .venv/bin/python -m pip install -r requirements-feishu.txt || { read '?安装失败，请检查网络 / Installation failed. Check network. Press Return.'; exit 1; }
fi
.venv/bin/python app.py --live --feishu-listen --open
if [[ $? -ne 0 ]]; then
  read '?启动未完成，请查看上方提示 / Startup failed; check the message above. Press Return.'
fi
