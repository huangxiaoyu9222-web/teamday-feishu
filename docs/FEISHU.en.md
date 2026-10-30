# Feishu connection: send first, then use numeric replies

[简体中文](FEISHU.md) · **English** · [Usage](USAGE.en.md)

You need permission to create an enterprise custom application, obtain organization approval, and include intended members in its availability scope. TeamDay currently uses mainland Feishu endpoints at `open.feishu.cn`; international Lark domain switching is not implemented.

## 1. Create an application and enable its bot

Create an enterprise custom app in the [Feishu developer console](https://open.feishu.cn/app). Add the bot capability, obtain App ID and App Secret, and enter them in the local `.env`:

```dotenv
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
```

These are placeholders. Never put real credentials in docs, screenshots or GitHub.

## 2. Request message permissions and subscribe to events

Request:

- `im:message:send_as_bot` to send messages as the app.
- `im:message.p2p_msg:readonly` to receive users' private messages to the bot.

Subscribe to `im.message.receive_v1` and choose long-connection event delivery. Console labels may change; consult official [Send message](https://open.feishu.cn/document/server-docs/im-v1/message/create) and [Receive message](https://open.feishu.cn/document/server-docs/im-v1/message/events/receive) documentation.

TeamDay uses the official Python SDK's outbound WebSocket. No public HTTP callback, tunnel or group-reading permission is required. Only mapped users' private text messages are handled; groups, audio, images and files are ignored.

Publish an app version and complete your organization's approval/enablement process. Make sure intended members are in scope. After modifying permissions/events, check that the changes are published; saving settings alone may not activate them.

## 3. Start the connection

On macOS, use `启动真实连接.command`. It opens `.env` on first launch and automatically prepares the optional SDK environment on a later launch. Alternatively:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-feishu.txt
python3 app.py --live --feishu-listen --open
```

Configure model credentials, model name and compatible base URL as explained in [Usage](USAGE.en.md). Restart after changing `.env`.

If the console requires an active connection before saving event settings, keep TeamDay running while saving them. The listener and scheduler require this process to remain running and the computer to stay awake.

## 4. Bind member open_id values

An `open_id` identifies a user **within this application**. A name, phone number, `user_id`, or another app's `open_id` cannot replace it.

Ask your administrator to obtain IDs through the current app's API explorer and an allowed directory endpoint. Extra permissions/data scope may be required for that endpoint. Authorized event-debugging tools can also expose `sender_id.open_id`. Avoid requesting broad directory access merely to guess an ID.

TeamDay does not automatically register users or log unknown user IDs. Messages from unmapped users are ignored by the listener. Sending “hello” does not enroll someone.

In the local administrator console, open 团队设置, fill each member's 飞书 open_id, and save. Check that name, role and focus match the correct person. Ordinary members interact in Feishu private chat.

## 5. Test a deliberate send

1. Select a configured test member in live mode.
2. Refresh the morning briefing and review its content.
3. Choose 发送简报到飞书 to send it to that member's configured `open_id`.
4. Verify receipt in Feishu, then inspect the local delivery result.

`sent` means the API confirmed sending, not reading. For failures, check credentials, bot capability, permissions, published version, availability scope and ID. For timeouts, inspect the actual chat before deciding nothing was sent. Repeated clicks reuse the same card's delivery. Refreshing creates a new version that can be explicitly sent.

## 6. Generate a draft by number

With the listener running, a bound member can send `早报` (morning brief), `简报` (brief) or `午报` (midday brief). The bot's command vocabulary and replies are currently Chinese.

Reply with `1`, `2`, etc. to generate an action draft. To identify a card explicitly, reply:

```text
actualCardID 1
```

Replace the placeholder with the returned card ID. A bare number refers to the latest associated card. Do not use numbers from an expired/replaced card. Results return as text and remain in the local artifact view for Markdown download. Duplicate events reuse recorded results.

Arbitrary natural language is not treated as an executable command. A member name in a message cannot override sender identity. Intake, knowledge confirmation and team configuration take place in the local administrator console.

## 7. Optional Bitable writeback

First validate private-chat generation. Artifacts containing private note context, including todos derived from private notes, skip shared-table writeback.

Give the app edit access to a Bitable and create these **five plain-text fields with exactly these Chinese names**:

| Exact field name | Stored value |
| --- | --- |
| 任务 | Action title |
| 成员 | Configured member name |
| 状态 | 初稿待审 (Draft awaiting review) |
| 成果ID | Unique local artifact ID |
| 内容 | First 10,000 characters of the draft |

Request the permission required by [Create record](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/create), and separately grant the app access to the actual table. API permission alone does not grant document access.

Set and restart:

```dotenv
FEISHU_BITABLE_APP_TOKEN=your_bitable_app_token
FEISHU_BITABLE_TABLE_ID=your_table_id
```

The Bitable app token identifies the target document, not the bot's App ID. Writeback failures are reported separately; local results remain saved. Creation is not automatically retried to avoid duplicate records. This is artifact export, not full knowledge-base synchronization.

## 8. Enable scheduling last

After manual delivery and numeric replies work, enable scheduling in 团队设置. Example times are 08:00 and 13:00 in Asia/Shanghai. The service checks while running and catches up only within one hour. Monday–Friday filtering is optional; public holidays are not calculated. Automatic failed attempts are spaced at least five minutes apart, with at most three attempts per card.

## Troubleshooting

| Symptom | Check first |
| --- | --- |
| Demo cannot send | Start with `--live`; demo prohibits external sending |
| Sending works but numeric replies do not | `--feishu-listen`, SDK, event subscription, published settings, app-scoped open_id |
| No inbound events | Private-message permission, event subscription, availability scope, app version |
| Draft generation fails | Model base URL, key, name and compatible response; configured indicator is not a connectivity test |
| No morning catchup after restarting | The one-hour catchup window may have passed |
| No Bitable record | Private-source skip, writeback outcome, field names, API/document permissions, token/table ID |
| Initial setup needs approval | The enterprise administrator controls app approval and availability |

Some official documentation pages are client-rendered. Open them directly in a browser if a text reader cannot display their contents.
