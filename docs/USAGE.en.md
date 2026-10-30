# Using TeamDay

[简体中文](USAGE.md) · **English** · [Feishu setup](FEISHU.en.md)

Run commands from the extracted project folder. Requires Python 3.9+ on macOS / Linux; use WSL on Windows. The application interface and generated drafts are currently Chinese. Both installation and usage documentation are bilingual.

## 1. Try the complete demo

```bash
python3 app.py --open
```

Visit `http://127.0.0.1:8765` if necessary. **演示模式 · 合成数据** means Demo mode · Synthetic data. The demo uses fictional people and organizations with local templates, no model requests, no feed fetching and no Feishu sending. On macOS, double-clicking `启动演示.command` is equivalent.

| Interface label | Meaning and action |
| --- | --- |
| 今日简报 | Today: morning/midday briefings and personal tasks |
| 更新早间简报 / 更新午间简报 | Refresh morning / midday briefing |
| 交给助手推进 | Draft actions the assistant can prepare |
| 生成草稿 1 / 查看成果 | Generate draft 1 / View artifact |
| 留给你的决定 | Tasks and decisions for you |
| 标记完成 / 暂缓 / 重新开启 | Complete / Snooze until tomorrow / Reopen |
| 现场记录 | Field notes: intake, review and confirmation |
| 整理并预览 | Prepare a draft preview; does not add confirmed knowledge |
| 确认并保存知识 | Confirm reviewed content and save knowledge |
| 仅本人 / 团队共享 | Private to this member / Shared with the team |
| 成果 | Saved artifacts |
| 团队设置 | Team settings; administrator setup |
| 已配置 | Credentials are present; connection has not necessarily been tested |
| 已启用 | Feature enabled in the running service |

Switch members in the top right. Generate a numbered draft, review it, and download Markdown. Repeating the same action returns the existing artifact instead of generating duplicates.

To add a note, provide organization, project, participant identity clues, and a raw transcript. Preview it, correct the text and summary, and enter one personal todo per line. Check the review box and confirm. Then refresh the briefing to include the newly confirmed note. New note intake defaults to **private**; deliberately choose team sharing when appropriate.

Refresh creates a new snapshot. Use the numbers on the new card. Old cards delivered to Feishu can be selected explicitly with `cardID number`; undelivered replaced cards expire. Generation and Bitable writeback have separate outcomes. A writeback failure does not delete the local artifact.

Stop with Ctrl+C. Data persists in `data/`. If the port is occupied, use `python3 app.py --port 8766 --open`. Only one instance per mode is allowed.

## 2. Review identity and meaning

Raw text is retained. Corrections never overwrite it. Identify people by organization, function and role in this meeting. A matching name does not establish identity; participation does not establish purchasing authority. Label uncertain claims as unconfirmed.

Live mode with a configured model attempts correction and summary suggestions. If suggestions fail, the original remains available for manual editing. Demo mode requires manual correction. Only the note owner can confirm it. Confirmed todos belong to that owner; deadlines are not inferred. Confirmed notes are displayed read-only.

Confirmed shared notes may enter other members' context; private notes are scoped to the owning member. This is workflow scoping, not authentication: the trusted local administrator can switch members. Ordinary members should use their Feishu private chats.

## 3. Connect a real team

On macOS, double-click `启动真实连接.command`. It creates and opens `.env` if absent; fill it in and launch again. On the next run it creates `.venv` and installs the Feishu SDK if needed. Internet access is required for the initial SDK installation. Python must already be installed.

For manual setup, copy the example only if `.env` does not already exist:

```bash
cp .env.example .env
```

Edit it locally. Never commit credentials.

| Variable | Purpose |
| --- | --- |
| MODEL_BASE_URL | Chat Completions base URL, e.g. `https://api.openai.com/v1`; do not append `/chat/completions` |
| MODEL_API_KEY | Your model provider's key |
| MODEL_NAME | A model identifier actually available through that provider; required |
| MODEL_TIMEOUT | Optional timeout in seconds; default 60, clamped to 10–180 |
| FEISHU_APP_ID / FEISHU_APP_SECRET | Feishu enterprise custom app credentials |
| FEISHU_BITABLE_APP_TOKEN / FEISHU_BITABLE_TABLE_ID | Optional artifact table; leave blank if unused |

The provider must accept `POST {MODEL_BASE_URL}/chat/completions` and return text in `choices[0].message.content`. Remote URLs require HTTPS; local loopback models may use HTTP. A configured indicator only checks presence of credentials, not connectivity. Generate a real draft to validate your model.

Local-only live mode:

```bash
python3 app.py --live --open
```

With numeric replies in Feishu:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-feishu.txt
python3 app.py --live --feishu-listen --open
```

Follow the [Feishu guide](FEISHU.en.md) for permissions, publishing, member binding and a delivery test. Restart after editing `.env`. Live mode has a separate empty database and `config.json`; synthetic customer notes are not imported.

## 4. Customize the team and sources

In 团队设置, edit the team goal and each member's name, role, focus and app-scoped Feishu `open_id`. IDs must be unique and contain only letters, digits, `_` or `-`. Keep them stable after creating records. Do not reuse another app's `open_id`.

RSS / Atom sources are configured with name and URL fields. Use an actual feed URL, not an ordinary article page. Save, then choose 刷新来源 on Today. Matching uses keywords in member focus and the feed title/summary; it is not semantic research, full-text analysis or cross-verification. No automatic video analysis is included.

## 5. Validate sending before enabling a schedule

Select a member with a bound `open_id` in live mode. Refresh and review the briefing, choose 发送简报到飞书, then check the actual Feishu private chat. The button is unavailable in demo mode or when app/recipient configuration is missing. `sent` means Feishu confirmed the API request, not that the recipient read it.

Scheduling defaults to off. After manual delivery succeeds, enable it in settings and choose morning/midday times, an IANA timezone (default `Asia/Shanghai`), and weekdays-only if desired. Weekdays means Monday–Friday, not a jurisdiction's public-holiday calendar.

The service checks about every 30 seconds and catches up only within one hour after the scheduled time. Sleeping computers and stopped services do not send. A scheduled run refreshes feeds and the briefing before its first delivery attempt. At most three attempts are made per card; automatic retries are at least five minutes apart. Success or an interrupted in-flight result is not blindly resent. Clicking send repeatedly on the same version reuses its delivery; explicitly sending a refreshed version sends the new card. Scheduling does not resend a slot already delivered that day.

## 6. Data, outputs and sharing

SQLite stores notes, briefings, todos, artifacts and delivery history locally. Model calls send relevant context to your configured provider. Feishu delivery and optional Bitable writeback transmit corresponding content to Feishu. Artifacts using private notes or todos derived from private notes are not automatically written to a shared Bitable.

The web service is a local administrator console, not a remote multi-user portal. Keep `data/`, `.env`, `config.json`, `config.demo.json` and `.venv/` out of public source. Back up runtime data separately. The release ZIP contains only clean source and placeholder examples.

## 7. Current scope

Artifacts are Markdown drafts, not formatted slides or PDF documents. Meeting actions prepare agendas/invitation wording, without checking availability or sending invitations. Transcripts are pasted; recording hardware is not connected. Feishu knowledge-base sync, full chat ingestion, independently verified news and purchase/deployment commitments are not implemented. Generated text always needs review; no model can guarantee factual accuracy.
