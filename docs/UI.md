# TeamDay UI

A dependency-free, Chinese personal workspace: narrow fixed navigation, spacious daily brief, numbered executable actions, and a separate right-hand column for human decisions. Cool slate and blue establish hierarchy; restrained violet marks demonstration and human review. The interface becomes a single-column view below 800 px. System PingFang / Hiragino typography requires no font download.

## Views
- 今日简报: per-member morning/midday generation, execution and stored artifacts, task completion/snooze/reopen, feed refresh, explicit Feishu send button.
- 现场记录: context and identity clues, raw transcript, editable correction and summary, explicit review checkbox, newline-delimited owner-assigned todos, history.
- 成果: retained artifact detail and member-scoped download route (local administrator, no login authentication). Content renders as plain pre-wrapped text.
- 团队设置: guided team/member/schedule fields and name/URL feed fields. Secrets remain outside this UI.

## Behavior
All mutations use bootstrap CSRF token; fetch failures are visible, in-flight action buttons disable, all dynamic content uses textContent or form values. No injected user or model HTML. Demo labels distinguish synthetic/local-template outputs. Push buttons explicitly state recipient/effect; returned delivery state is displayed without claiming delivery success. Source URLs accept only HTTP(S). Member changes reset unfinished preview selection.

Contract follows DESIGN.md. Static files use /static/app.js and /static/style.css. JS syntax validated with bundled Node. Integration/browser validation should run against the completed backend.
