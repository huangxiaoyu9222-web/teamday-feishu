# TeamDay v0.1 — approved conversation design

Local-first, Chinese lightweight team personal assistant. One daily card per member, evidence-linked action suggestions, numeric execution, explicit human decisions. Shareable starter project, no cloud publishing in this task.

## Scope
- Zero-dependency Python 3.9+ local web app with SQLite persistent state; demo synthetic data isolated from live database.
- Roles FDE/product/engineering, editable team/member configuration, 08:00 and 13:00 schedule (Asia/Shanghai).
- Meeting intake: identity/context → raw vs corrected transcript → user confirmation → shared/private knowledge. Never infer confirmed identity from a name alone.
- Personalized daily brief with numbered draft-generation actions and human tasks. Execution owner checks, idempotence, real artifact stored and downloadable. Demo uses explicit local templates; live uses configured OpenAI-compatible chat endpoint.
- Feishu API send per-member brief; optional official SDK long connection receives private numeric replies. Persistent scheduled sends and bounded retry. Bitable optional record writeback is separately reported.
- RSS/Atom external signals, sources/freshness/verification limits clearly labeled, no fabricated news or verification.
- Local UI is a trusted administrator/demo console, not multi-tenant auth. Bind localhost only; origin/CSRF checks. Feishu sender is mapped to configured open_id.
- Calendar v0.1 produces meeting agenda and invitation draft, not real availability lookup/invite; audio handled by upstream transcript, not direct hardware integration. Full KB sync not promised.

## UI contract
GET /api/state?member=jade returns {mode,member,members,team,brief,notes,tasks,artifacts,news,connection,deliveries}. Members fields id,name,role,focus,open_id. brief {id,date,slot,greeting,headline,highlights:[{title,body,source}],actions:[{id,number,title,description,status,artifact_id}],signals:[]}. notes {id,org,project,people,raw,corrected,summary,status,visibility,owner,created_at}. tasks {id,owner,title,kind,status,source}. artifacts {id,title,body,mode,created_at}. connection boolean llm,feishu,listener, scheduler + detail.
GET /api/config => safe config incl team {name,goal}, members, schedule {enabled,morning,midday,timezone,weekdays_only}, feeds [{name,url}]. GET /api/bootstrap => {csrf}.
POST /api/brief {member,slot:'morning'|'midday'} => brief; deterministic same-day snapshot (no duplicate actions).
POST /api/execute {member,brief_id,number} => {artifact,status,writeback}. POST /api/task {member,id,status:'done'|'snoozed'|'open'} => task.
POST /api/notes/preview {member,org,project,people,raw,visibility:'team'|'private'} => note.
POST /api/notes/confirm {member,id,corrected,summary,todos:[string]} => note. Only owner can confirm; todo assigned to confirming owner with no inferred deadline.
POST /api/config safe config => config. POST /api/news/refresh {} => {items,errors}. POST /api/push {member,slot} => delivery (explicitly sends to configured Feishu recipient).
GET /api/artifact?id=...&member=... => {artifact}; GET /download?id=...&member=... => text/markdown attachment.
All mutations JSON, X-CSRF-Token from bootstrap; same-origin only. Non-2xx JSON {error:human-readable}. No external HTML rendering; escape user content.
