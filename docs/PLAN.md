# TeamDay Implementation Plan

Goal: deliver a runnable daily-brief and execution workflow with an honest demo mode and configurable Feishu connectors.
Architecture: Python stdlib HTTP server, SQLite domain service, static browser interface, independent connector module, optional lark-oapi listener.
Spec: DESIGN.md

- [x] Core: write regression tests for member isolation, duplicate execution, draft/confirmed knowledge, repeat ingestion, schedule persistence; implement store and service.
- [x] Connectors: test Feishu response failures, RSS parsing, model failure and URL boundaries; implement network adapters and long-connection entry point.
- [x] Interface: Chinese responsive daily workspace, intake correction, tasks, artifacts and configuration; all controls use API contract.
- [x] Integration: HTTP origin/CSRF checks, localhost binding, scheduler outbox with retry, Feishu sender mapping; run tests.
- [x] Delivery: README quick start, Feishu permissions and model setup, SKILL.md, clean ZIP without secrets/data, launch and browser review.

Verification: python3 -m unittest discover -s tests -v; browser exercise role switching → brief → execute twice → artifact → intake → confirm → reload; fake-transport connector tests, no claims of real Feishu verification without credentials.
