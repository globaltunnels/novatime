# NovaTime — Business Plan, Marketing Plan, Design Specification & Implementation Plan (v1.0, Aug 26, 2025)

*This document is written for both humans and AI agents. It combines the “why” (business & marketing) and the “how” (product/engineering spec) so an AI development pipeline can act directly on it. All deep technical details are moved to the **Appendix**.*

---

## 0) Executive Summary

NovaTime is a unified, AI-first platform for **time tracking**, **task & project ops**, **frontline attendance**, and **team chat with @ai**. It merges the best of Clockify, Toggl, Harvest, Connecteam, and Buddy Punch into one privacy-forward product with explainable **Performance Intelligence** (predictability, focus fragmentation, schedule adherence) and **AI-managed planning & assignment**.

**Why now:** Remote & hybrid work remain entrenched; time & attendance digitization and AI-assisted workflows are accelerating. Market estimates vary but consistently project double-digit CAGR for time-tracking software into the next decade. ([Straits Research][1], [Fact.MR][2], [Technavio][3])
Hybrid/remote work persists at meaningful levels in 2024–2025, sustaining demand for flexible time/attendance and desk-plus-frontline workflows. ([Bureau of Labor Statistics][4], [Backlinko][5], [Robert Half][6], [Business Insider][7])

**Positioning:** “From clock-in to cash-in. Time that fills itself.” We win by (1) **AI that drafts timesheets & plans**, (2) **explainable insights** managers can trust, (3) **one tool** for timers + shifts + chat + lightweight PM, and (4) **privacy-first** controls.

---

## 1) Product Overview

### 1.1 Project Goals

* Remove friction from time capture and approvals across **desk** and **frontline** teams.
* Provide **explainable performance** insights (not spyware) to improve predictability, utilization, and budget health.
* Tie **Tasks ↔ Time ↔ Billing** and **Chat ↔ @ai** so work planned is work accounted.
* Offer **AI-managed planning & assignment** that respects skills, capacity, time zones, and fairness.

### 1.2 Target Audience

* **Agencies & pro services** (billable time, budgets, invoicing).
* **Field/shift teams** (construction, healthcare, retail) needing kiosk, GPS, breaks & OT policies.
* **Product/engineering teams** needing zero-friction timers and integrations (Jira/GitHub/Slack).

### 1.3 Key Features (high level)

* **Magic Timesheets** (AI draft from calendar, tickets, commits) with human-in-the-loop review.
* **Performance Intelligence**: Predictability Index, Focus Fragmentation, Schedule Adherence, Timesheet Quality; cohort-fair, explainable.
* **Projects/Epics/Sprints & AI assignment** with capacity, skills, and deadlines.
* **Frontline attendance**: kiosk (PIN/QR/FaceID), GPS/geofences, breaks, offline-first.
* **Approvals & policies**, **invoicing & exports** (QBO/Xero/payroll).
* **Chat & @ai**: summarize threads, extract tasks, create updates, answer “where are we?”
* **AI-driven SEO marketing** (Next.js SSG/ISR, Headless CMS, A/B tests).
* **Easy identity**: OIDC social login + passkeys/WebAuthn. ([OpenID Foundation][8], [Microsoft Learn][9], [FIDO Alliance][10])

---

## 2) Functional Requirements

### 2.1 User Stories (samples)

* **Time capture (desk):** “As a developer, I want 1-tap start/stop on my current task so I don’t lose time context.”
* **Attendance (frontline):** “As a site worker, I want geofenced clock-in via kiosk so compliance is automatic.”
* **Approvals:** “As a manager, I want an exceptions queue with reasons so I can approve 90% in bulk.”
* **Performance:** “As a team lead, I want explainable insights and one coaching tip weekly so I can improve predictability fairly.”
* **AI planning:** “As a PM, I want AI to auto-assign sprint work respecting skills & capacity so delivery risk drops.”
* **Chat-to-task:** “As a teammate, I want to convert a message into a task with estimates in one click.”
* **Marketing:** “As a visitor, I want an ROI calculator and competitor comparisons so I can justify switching.”
* **Identity:** “As an admin, I want OIDC/SSO and passkeys so sign-in is simple and phishing-resistant.” ([OpenID Foundation][8], [FIDO Alliance][10])

### 2.2 Feature Breakdown (condensed)

* **Time & Timesheets**: timers, manual/bulk entry, idle detection, week grid, submit/lock, multi-level approvals.
* **Frontline**: shifts, kiosk PIN/QR/FaceID, geofences, breaks/overtime policies, offline queue.
* **Projects/Tasks**: Kanban + timeline, estimates, dependencies, templates; **AI assignment** (skills, capacity, priority).
* **Reports/Insights**: utilization, job costing, profitability; Performance Intelligence scorecards.
* **Chat**: channels/threads, mentions, files; **@ai**: summarization, extraction, suggested actions.
* **Marketing SEO**: CMS-driven pages, schema.org FAQ, comparison pages, A/B tests; follows Google Search Essentials. ([Google for Developers][11])
* **Identity**: **OIDC** providers + **passkeys/WebAuthn**; SAML/SCIM for enterprise. ([OpenID Foundation][8], [FIDO Alliance][12])

### 2.3 Data Flow (overview)

1. **Signals** (calendar, commits, tickets, geofence, kiosk) → **Ingestion** → **Feature Store**.
2. **AI Drafts** (timesheets, plans) → **Human Review** → **Approvals → Exports**.
3. **Events** (chat/messages/tasks/time) → **Insights** (KPIs, anomalies) → **Manager actions** (approve, reassign, coach).
4. **Pre-login** CMS content → **SEO render** → **lead capture** → **trial onboarding**.

---

## 3) UI/UX

### 3.1 Wireframes & Mockups

Low-fi wireframes are provided as **SVG** and **PNG**, plus an **HTML storyboard**:

* **Storyboard (HTML):** [novatime\_storyboard.html](sandbox:/mnt/data/novatime_storyboard.html)
* **Wireframes (SVG, crisp):** [novatime\_wireframes\_svg\_v1.zip](sandbox:/mnt/data/novatime_wireframes_svg_v1.zip)
* **Wireframes (PNG):** [novatime\_wireframes\_v1.zip](sandbox:/mnt/data/novatime_wireframes_v1.zip)

Screens include: Marketing Home, Home/Today, Task Board, Planning Timeline, Chat with **@ai**, Weekly Timesheet, Approvals, Reports, Kiosk, Worker 360, Team Heatmap, Anomaly Radar.

### 3.2 Navigation

Primary: **Home**, **Timesheet**, **Projects**, **Tasks**, **Schedule**, **Approvals**, **Reports**, **Chat**, **Admin**.
Mobile: bottom nav; all flows PWA-ready.

### 3.3 Branding & Style Guide (essentials)

* **Tone:** Calm confidence.
* **Typography:** Inter/System; Display 36/44; Body 16/24.
* **Palette:** Primary #2563EB; Accent #22C55E; Warning #F59E0B; Error #EF4444; Surfaces Dark #0B1220 / Light #F8FAFC.
* **Motion:** 200–300ms ease-out; reduced-motion variants.

### 3.4 Accessibility

Target **WCAG 2.2 AA** (AAA for core text); keyboard-first paths, ARIA for complex tables, high-contrast themes, RTL locales. ([W3C][13])

---

## 4) Technical Requirements

### 4.1 Platform / Stack

* **Backend:** Python **Django + DRF**, Celery, Channels (WS).
* **DB:** **PostgreSQL** (+ PostGIS for geofences). Cache: **Redis**. Storage: S3-compatible.
* **Frontend:** **React** + Tailwind/MUI; **PWA**. Mobile: React Native (post-MVP).
* **Analytics/ML:** Event ingestion → Feature store → anomaly detection + explainability.
* **SEO Frontend:** Next.js (SSG/ISR) + Headless CMS (Wagtail/Strapi). Follows Google SEO Starter Guide. ([Google for Developers][11])
* **Identity:** **OIDC** (social/enterprise), **passkeys/WebAuthn**, **SAML/SCIM**. ([OpenID Foundation][8], [Microsoft Learn][9], [FIDO Alliance][12])

### 4.2 Database (high-level)

Entities: Org, Workspace, Team, User; Client, Project, Epic/Sprint, Task; Assignment; TimeEntry; Timesheet; Policy; Shift/Location/Geofence; Approval; Rate/Budget; Invoice/Expense; Conversation/Channel/Message; AIInvocation; FeatureToggle; PromptTemplate; SEOAsset; ABTest; MetricDefinition; PerformanceSnapshot; BenchmarkCohort; InsightCard.

### 4.3 APIs

* **OpenAPI (v1.1 expanded):** [novatime\_openapi\_v1.1.yaml](sandbox:/mnt/data/novatime_openapi_v1.1.yaml)
* **Swagger UI bundle:** [novatime\_swagger\_ui\_bundle.zip](sandbox:/mnt/data/novatime_swagger_ui_bundle.zip)
  Endpoints cover **Tasks/Assignments**, **Time/Timesheets/Approvals**, **Conversations/Messages**, **AI invoke**, **SEO/AB tests**, **Insights**, **Auth** (magic link, OIDC, passkeys).

### 4.4 Performance & Scalability

* P95 page ≤ 1.5s; Home/Today ≤ 1.0s; PWA offline queues; background sync.
* Scale path: extract Chat, Tasks, Insights into services; add Kafka; orchestration via Temporal (phase 2).

---

## 5) Non-Functional Requirements

**Security:** Tenant isolation; encryption in transit/at rest; secrets in KMS; audit logs immutability.
**AuthN/AuthZ:** OIDC SSO, passkeys/WebAuthn, MFA; RBAC & SCIM. ([OpenID Foundation][8], [FIDO Alliance][12])
**Privacy:** No screenshots/keystrokes by default; worker transparency center; opt-in for sensitive modules.
**Reliability:** 99.9% target; graceful offline; idempotent exports; outbox pattern.
**Compliance:** GDPR/CCPA, WCAG 2.2 AA, SOC-aligned controls. ([W3C][13])

---

## 6) Software Architecture Document (SAD)

### 6.1 System Components

* **Time Service** (timers, entries, idle).
* **Schedule/Attendance** (shifts, kiosk, geofence).
* **Policy Engine** (OT/breaks/rounding).
* **Approvals** (states, comments, audit).
* **Billing** (rates, budgets, invoices, exports).
* **Tasks/Projects** (kanban, timeline, dependencies, templates).
* **AI Planning** (capacity/skills/priority solver).
* **Chat** (channels/threads, semantic search).
* **Insights** (features, cohorts, explainers, anomalies).
* **Integration Hub** (calendar, Jira/GitHub, Slack/Teams, QBO/Xero, payroll).
* **Marketing CMS** (SEO assets, A/B).
* **Identity** (OIDC/passkeys/SAML/SCIM). ([OpenID Foundation][8], [FIDO Alliance][12])

### 6.2 Data Models

See **Appendix A** for full entity list and sample YAML contracts.

### 6.3 APIs & Integrations

OpenAPI + webhooks; OAuth apps for Jira/GitHub/Slack/Drive; SEO sitemap/feeds; OIDC discovery and dynamic client registration where supported. ([OpenID Foundation][14])

### 6.4 Tech Decisions (why)

* **Django** for rapid CRUD, policies, and RBAC; **React** for UX velocity and PWA.
* **OIDC + passkeys** for secure, user-friendly login and lower fraud. ([OpenID Foundation][8], [FIDO Alliance][10])
* **Explainable AI** preferred over opaque scoring to build trust.

---

## 7) API Documentation (pointer)

Use **Swagger UI** to explore live endpoints and schemas:

* OpenUI: unzip & open `index.html` → [novatime\_swagger\_ui\_bundle.zip](sandbox:/mnt/data/novatime_swagger_ui_bundle.zip)
* Direct YAML: [novatime\_openapi\_v1.1.yaml](sandbox:/mnt/data/novatime_openapi_v1.1.yaml)

---

## 8) Coding Standards & Guidelines

* **Backend:** PEP-8 + mypy/ruff; DRF serializers & viewsets; 12-factor config.
* **Frontend:** TypeScript strict; state via RTK/Query; hooks-first; accessibility linting; Lighthouse budgets.
* **Testing:** pytest + factory\_boy; Playwright E2E; contract tests for APIs; dbt tests for metrics.
* **Observability:** OpenTelemetry traces; structured logs with org/user correlation.

---

## 9) QA & Testing

### 9.1 Test Plan

* **Functional:** unit + integration + E2E (desk timer; kiosk offline; approvals; AI draft confirm).
* **Performance:** load (1k concurrent), sync under flaky mobile networks.
* **Security:** auth flows (OIDC, passkeys), rate limits, data isolation.
* **Accessibility:** keyboard paths, contrast, screen reader. WCAG 2.2 AA. ([W3C][13])

### 9.2 Environments

Dev → Staging → Prod with seeded demo data & synthetic load. Dark launches behind flags.

### 9.3 Acceptance Criteria (Given/When/Then example)

* **Timesheet submit:** Given week entries are complete, When user clicks Submit, Then sheet locks and manager receives approval card with zero validation errors.

---

## 10) Marketing Plan

### 10.1 Market Sizing (triangulated)

* 2024–2035 projections show **double-digit CAGR**; estimates range from **\~\$8.4B (2025) → \~\$29.9B (2033)** and **\$3.8B (2025) → \$16.1B (2035)**, indicating robust growth but varied baselines across analysts. ([Straits Research][1], [Fact.MR][2])
* Additional analyses project strong 2025–2029 expansion at \~17% CAGR. ([Technavio][3])
* Persistent hybrid/remote work (≈23–30% of US workers partly remote; \~28% of days) sustains demand for flexible time/attendance. ([Backlinko][5], [Business Insider][7], [Barron's][15])

### 10.2 Competitive Takeaways

* **Clockify:** freemium, simplicity; advanced reporting often paid. ([Capterra][16])
* **Toggl Track:** UX polish and reports; freelancer/SMB skew. ([Toggl][17])
* **Harvest:** strong billing/invoicing; older IA patterns in places. (See reviews/compare pages.) ([Capterra][16])
* **Connecteam/Buddy Punch:** frontline strengths (scheduling/GPS/biometrics). (General reviews & vendor pages.)

### 10.3 Differentiation & Messaging

* **Explainable AI** performance + **AI planning & assignment** (capacity/skills/priority) — reduce variance and cycle time.
* **Unified Desk + Frontline** (timers + kiosk + geofence) — one source of truth.
* **Privacy-first** (no surveillance); cohort-fair benchmarks.
* **Marketing hooks:** **ROI calculator**, **competitor comparison hubs**, and **“Time that fills itself.”**

### 10.4 Channels & Tactics

* **SEO**: comparison pages, schema FAQ, use-case hubs, Lighthouse 95+, and Search Essentials. ([Google for Developers][11])
* **Content**: case studies (cycle time ↓, invoice corrections ↓), “manager’s playbook” for AI-coaching.
* **PLG**: frictionless trial/onboarding; import from CSV/Clockify/Toggl.
* **Partnerships**: accountants/QBO consultants; field ops associations.
* **Paid**: retargeting on comparison pages; ROAS-driven experiments.
* **Sales enablement**: demo using **Storyboard** and pre-baked dummy insights.

### 10.5 KPIs

* Organic signups, SEO page conversions, trial→paid, D7 activation (weekly submit), approval time ↓, invoice correction rate ↓.

**Assets:**

* **Storyboard:** [novatime\_storyboard.html](sandbox:/mnt/data/novatime_storyboard.html)

---

## 11) Implementation Plan (for AI + human teams)

### 11.1 Phasing (12 weeks MVP)

| Weeks | Scope (AI-automatable ★)                                                       |
| ----- | ------------------------------------------------------------------------------ |
| 1–2   | Auth (OIDC/magic link/passkeys★), Orgs & RBAC★, Projects/Tasks★, Time Entries★ |
| 3–4   | Weekly Timesheet★, Approvals★, Reports (basics)★                               |
| 5–6   | Budgets/Rates★, QBO export, Slack/Teams hooks★                                 |
| 7–8   | **Magic Timesheets** (calendar/Jira/GitHub ingest★), Home/Today UX★            |
| 9–10  | Kiosk (PIN/QR) + geofence + offline★                                           |
| 11    | Policy engine (OT/breaks/rounding) + Exceptions UI★                            |
| 12    | Hardening, A11y, i18n, beta launch                                             |

### 11.2 AI Work Packages

* **Scaffold** services (DRF viewsets, serializers, tests) from OpenAPI.
* **Generate** db schema & migrations from entity list; dbt models for metrics.
* **Wire** ingestion connectors (Calendar, Jira/GitHub, Slack) and unit tests.
* **Implement** explainers and anomaly detection with SHAP-like outputs.
* **Synthesize** demo data; seed fixtures for Storyboard demos.

### 11.3 Staging & Release

* Dev → Staging → Prod with data masking; dark-launch AI modules; region canaries; auto-rollback on SLO breach.

### 11.4 Internationalization & Mobile

* i18next (frontend), gettext (backend), Crowdin pipeline; RTL; locale switch in UI; PWA for mobile.

---

## 12) Risks & Mitigations

* **Privacy/bias** in performance analytics → transparency, cohort-fair benchmarks, model cards, manager training.
* **AI errors** → human-in-the-loop confirmation; evidence panel.
* **Scope creep** → strict MoSCoW, flags, milestone gates.
* **Offline conflicts** → sync ledger + last-write-wins with CRDT-like merge.

---

## 13) Metrics & Analytics

* **Adoption**: D1/D7 active, weekly submit rate, on-time submissions.
* **Value**: invoice cycle time, approval time, correction rate, utilization.
* **AI impact**: % accepted suggestions; delta in predictability and fragmentation.

---

# Appendix

## Appendix A — Technical Context (condensed index)

* **Performance Intelligence & Reporting** (Predictability, Focus Fragmentation, Schedule Adherence, Timesheet Quality; cohorts; explainers; APIs).
* **Task Management & AI Project Ops** (kanban/timeline, capacity planner, smart assignment, what-ifs, governance).
* **Social Authentication & Identity** (OIDC-first, passkeys/WebAuthn, SAML/SCIM, config-as-data). ([OpenID Foundation][8], [FIDO Alliance][12])
* **AI-Driven SEO Frontend** (Next.js SSG/ISR, CMS, AB tests, schema.org; Google Search Essentials). ([Google for Developers][11])
* **Collaboration & Live Chat with @ai** (threads, semantic search, summaries, /commands).
* **SDLC & Workflow Orchestration** (Phase 1: django-fsm/Celery; Phase 2: Temporal/Kafka).
* **Staging & Release Strategy** (flags, canaries, masking, demo mode).
* **Internationalization & Mobile** (i18n/RTL; PWA offline).
* **Frontend Enhancements** (Task board, Planning view, Chat-to-Task, Marketing home).

> See earlier design canvas for deep detail (already captured in your workspace). Wireframes and OpenAPI below.

---

## Appendix B — Initial Data Contracts (YAML excerpts)

```yaml
Task:
  id: ulid
  project_id: string
  title: string
  description: string
  status: [todo, in_progress, review, done, blocked]
  priority: [P1, P2, P3]
  estimate_hours: number
  due_at: datetime
  labels: [string]
  dependencies: [task_id]
  created_by: user_id
  updated_at: datetime

Assignment:
  id: ulid
  task_id: task_id
  user_id: user_id
  role: [owner, reviewer, assistant]
  load_percent: number  # 0..100
  start_at: datetime
  end_at: datetime
  source: [manual, ai]
  created_at: datetime

Conversation:
  id: ulid
  channel_id: string
  subject_ref: { type: [task, project, general], id: string }
  visibility: [internal, org, private]
  retention_days: number

Message:
  id: ulid
  conversation_id: string
  author_id: string | "@ai"
  text: string
  mentions: [string]
  attachments: [{ id: string, name: string, url: uri }]
  created_at: datetime
  thread_id: string | null

SEOAsset:
  id: ulid
  slug: string
  locale: string
  title: string
  content_md: string
  keywords: [string]
  schema_type: [article, faq, comparison, calculator]
  publish_state: [draft, review, published, ab_test]
  ab_test_id: string | null
  updated_at: datetime
```

---

## Appendix C — API Stubs & Assets

* **OpenAPI (v1.1, security/pagination/errors):** [novatime\_openapi\_v1.1.yaml](sandbox:/mnt/data/novatime_openapi_v1.1.yaml)
* **Swagger UI static bundle (zip):** [novatime\_swagger\_ui\_bundle.zip](sandbox:/mnt/data/novatime_swagger_ui_bundle.zip)

---

## Appendix D — Wireframes & Storyboard

* **Storyboard (HTML):** [novatime\_storyboard.html](sandbox:/mnt/data/novatime_storyboard.html)
* **Wireframes (SVG):** [novatime\_wireframes\_svg\_v1.zip](sandbox:/mnt/data/novatime_wireframes_svg_v1.zip)
* **Wireframes (PNG):** [novatime\_wireframes\_v1.zip](sandbox:/mnt/data/novatime_wireframes_v1.zip)

---

## Appendix E — Accessibility, Identity & SEO References

* **WCAG 2.2** & understanding docs. ([W3C][13])
* **Google SEO Starter Guide / Search Essentials.** ([Google for Developers][11])
* **OpenID Connect Core** & platform docs. ([OpenID Foundation][8], [Microsoft Learn][9])
* **Passkeys / FIDO / WebAuthn overview.** ([FIDO Alliance][10])

---

## Appendix F — Market Sources (selection)

* Time-tracking software market growth & size (multiple analysts for range triangulation). ([Straits Research][1], [Fact.MR][2], [Technavio][3])
* Remote/hybrid work prevalence & impacts. ([Bureau of Labor Statistics][4], [Backlinko][5], [Robert Half][6], [Business Insider][7], [Barron's][15])
* Competitive reviews (features & gaps). ([Capterra][16], [Toggl][17])

---

### Notes on Sources

Market numbers vary by methodology; we present **ranges** with citations to avoid over-precision. Accessibility and identity standards reference **primary sources** (W3C, OpenID Foundation, FIDO Alliance, Google).

---

**End of document.**

[1]: https://straitsresearch.com/report/time-tracking-software-market?utm_source=chatgpt.com "Time Tracking Software Market Size, Growth & Trends ..."
[2]: https://www.factmr.com/report/time-tracking-software-market?utm_source=chatgpt.com "Time Tracking Software Market Share and Statistics 2035"
[3]: https://www.technavio.com/report/time-tracking-software-market-analysis?utm_source=chatgpt.com "Time Tracking Software Market Size 2025-2029"
[4]: https://www.bls.gov/opub/btn/volume-13/remote-work-productivity.htm?utm_source=chatgpt.com "The rise in remote work since the pandemic and its impact ..."
[5]: https://backlinko.com/remote-work-stats?utm_source=chatgpt.com "14 Remote Work Statistics for 2025"
[6]: https://www.roberthalf.com/us/en/insights/research/remote-work-statistics-and-trends?utm_source=chatgpt.com "Remote Work Statistics and Trends for 2025"
[7]: https://www.businessinsider.com/big-firms-push-rto-small-startups-recruit-talent-young-workers-2025-7?utm_source=chatgpt.com "Small companies' pitch to workers: No RTO required"
[8]: https://openid.net/specs/openid-connect-core-1_0.html?utm_source=chatgpt.com "OpenID Connect Core 1.0 incorporating errata set 2"
[9]: https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc?utm_source=chatgpt.com "OpenID Connect (OIDC) on the Microsoft identity platform"
[10]: https://fidoalliance.org/passkeys/?utm_source=chatgpt.com "Passkeys: Passwordless Authentication"
[11]: https://developers.google.com/search/docs/fundamentals/seo-starter-guide?utm_source=chatgpt.com "SEO Starter Guide: The Basics | Google Search Central"
[12]: https://fidoalliance.org/specifications/?utm_source=chatgpt.com "User Authentication Specifications Overview"
[13]: https://www.w3.org/TR/WCAG22/?utm_source=chatgpt.com "Web Content Accessibility Guidelines (WCAG) 2.2"
[14]: https://openid.net/developers/specs/?utm_source=chatgpt.com "Explore All Specifications"
[15]: https://www.barrons.com/articles/work-from-home-economy-productivity-nicholas-bloom-726403ac?utm_source=chatgpt.com "Work From Home Arrangements Are Here to Stay. An Economist Weighs In on Their Merits."
[16]: https://www.capterra.com/compare/75598-169607/Harvest-vs-Clockify?utm_source=chatgpt.com "Compare Harvest vs Clockify 2025"
[17]: https://toggl.com/blog/best-time-tracking-software-for-developers?utm_source=chatgpt.com "7 Best Time Tracking Software Apps For Developers (2025 ..."
