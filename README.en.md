# TeamDay · Your team's next move, delivered in Feishu

**One daily brief. One number to reply. A working draft for what comes next.**

Turn reviewed meeting notes, personal tasks and relevant reading into a daily briefing for each teammate. Reply with a number in Feishu to prepare an interview outline, handoff brief, product assessment or meeting agenda—ready for human review.

[简体中文](README.md) · **English** · [Try the demo](#try-it-in-one-command) · [Connect Feishu](docs/FEISHU.en.md) · [Usage guide](docs/USAGE.en.md)

![TeamDay demo: Jade's daily workspace](docs/images/demo.png)

## From field notes to the next step

- **Explain it once.** Paste a transcript, check the organization, project and participant identities, and confirm the record before it becomes team context. The original stays available.
- **Know what needs attention.** Morning and midday briefings combine reviewed context, personal tasks and feed candidates matched to each member's focus.
- **Reply with a number.** Choose `1` or `2` in Feishu private chat to generate a reviewable draft for the selected action.
- **Keep decisions in human hands.** Review sources, download drafts, complete or snooze tasks, and choose private or shared notes.

Illustrative conversation using a synthetic scenario:

```text
TeamDay → Jade
First, confirm which field data we have permission to use.

I can prepare:
1. An outline for the next field interview
2. A cross-team handoff brief

Jade → 1
TeamDay → Returns a draft with source references and open questions.
```

The application interface, bot commands and generated drafts are currently **Chinese**. The English conversation above illustrates the interaction; the [English usage guide](docs/USAGE.en.md) maps the actual interface labels.

## Try it in one command

Requires **Python 3.9+ on macOS or Linux**. Windows users can use WSL. From the project folder:

```bash
python3 app.py --open
```

Visit `http://127.0.0.1:8765` if the browser does not open. On macOS, you can double-click `启动演示.command`. No account, API key, dependency installation or frontend build is needed for the synthetic demo. It uses local templates, makes no model calls and sends no Feishu messages.

Generate a draft, add and review a field note, then refresh the briefing to include it. Follow the [complete usage guide](docs/USAGE.en.md) for the rest.

## Bring your team into Feishu

On macOS, double-click `启动真实连接.command`. It creates and opens `.env` on first launch, then prepares the virtual environment and official SDK when launched again. One-time setup requires model credentials, an approved Feishu enterprise custom bot, and app-scoped member `open_id` values. Follow the [Feishu connection guide](docs/FEISHU.en.md).

Manual installation:

```bash
cp .env.example .env
# Edit .env locally. Do not overwrite an existing credential file.
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-feishu.txt
python3 app.py --live --feishu-listen --open
```

Validate delivery and numeric replies for one member before enabling schedules. Example times are **08:00 / 13:00 on weekdays**, with configurable times and timezone. The service must remain running. Demo and live data are separate.

## Scope of the preview

v0.1.0 includes optional RSS / Atom candidates, Feishu private-chat delivery and numeric replies, and Bitable artifact writeback. Feed matching uses focus keywords; candidates are not independently fact-checked.

Outputs are **Markdown drafts**. Calendar availability, invitation sending, recording hardware, PowerPoint/PDF export and automatic Feishu knowledge-base sync are not included. Your real model provider and Feishu tenant require installation-specific verification.

The browser is a trusted local administrator console without multi-user login isolation. Ordinary members use mapped Feishu private chats. Keep `.env`, `data/`, `config.json`, `config.demo.json` and `.venv/` out of public source.

## Why TeamDay exists

TeamDay began with Jade's original workflow concept for field work and team operations: preserve what happened on site, then help the team act on it. Industrial AI is the starting point; team goals, roles, interests and feeds are configurable.

The first release focuses on one complete path: **field note → human review → daily brief → numbered draft → retained artifact.**

## Build with us

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_release.py
```

[Architecture](docs/ARCHITECTURE.md) · [Acceptance](docs/ACCEPTANCE.md) · [Release](docs/RELEASE.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [MIT license](LICENSE)
