---
name: teamday
description: Run or configure TeamDay, a local-first Feishu team daily briefing assistant with confirmed meeting context and numbered draft execution.
---

# TeamDay operator skill

Read README.md and docs/USAGE.md first. This repository is a runnable application plus skill instructions, not a standalone prompt that supplies credentials or scheduling automatically.

## Start
- Requires Python 3.9+ on macOS/Linux. No third-party package is needed for demo.
- In this skill folder run `python3 app.py --open`. App binds only 127.0.0.1:8765. If already running open the existing URL; do not kill arbitrary processes.
- Use `--port 8766` if a different application occupies the port.
- Demo uses synthetic records and templates; label its outputs demo. Never send demo records to Feishu.

## Connect a real team
- Follow docs/FEISHU.md. User configures secrets in local .env; do not print its contents or commit it.
- Install optional dependencies in local .venv, then run `.venv/bin/python app.py --live --feishu-listen --open`.
- Live has a separate database and configuration. Bind each recipient's app-scoped open_id in the local administrator console.
- Scheduling is initially off; enable only when the user has authorized recurring sends to the configured recipients. Explain that the process must stay running and the computer awake.
- Saving configuration is not proof of connectivity. A real send must return a Feishu message_id before claiming delivery.

## Workflow
Use the UI or same-origin local JSON API. GET /api/bootstrap provides CSRF token; POST requests require X-CSRF-Token and Content-Type: application/json.
1. Select member; enter note with org, project, people, original transcript, visibility.
2. Review proposed corrected text, unresolved identity/speaker uncertainties and summary. Confirm only user-approved corrections. Do not infer authorizations from transcript.
3. Refresh daily brief; choose numbered draft action. Polling/repeating execution returns existing result, not a second artifact.
4. Confirm personal tasks or defer them from the task panel.
5. Download Markdown drafts; human review is still needed before using externally.

## Boundaries
- Local UI is a trusted operator console with role switching, not authenticated multi-user web hosting. Do not expose its port to the Internet.
- Feishu execution maps private message sender open_id to a member; do not accept a user-supplied member id as identity.
- The app does not directly read recording hardware, continuously synchronize Feishu knowledge bases, query busy calendars, send meeting invites, produce PowerPoint binaries, or independently verify all news claims.
- RSS output is candidate information with links and verification status, not guaranteed high-quality or cross-verified news.
- Scheduled cards take a daily snapshot. A manual refresh supersedes old actions. Never claim generated draft means business task completed.

## Verify
Run `python3 -m unittest discover -s tests -v`. External connector tests use fake transport; they do not prove a real user's permissions.
