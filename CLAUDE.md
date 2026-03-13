# CLAUDE.md — Migravio

> You are building **Migravio** — an AI-powered immigration legal platform for the U.S. market.
> Read this file fully before writing a single line of code. This is the source of truth.
> When in doubt, ask. When scope is unclear, build less and confirm.

---

## What Is Migravio?

Migravio helps immigrants in the United States navigate the immigration system — in their own language, affordably, without needing a lawyer for every question.

**The problem**: 51.9M immigrants face a $9.9B legal services market that is expensive, slow, English-only, and inaccessible. Most questions don't need a lawyer — they need a knowledgeable, trusted friend who speaks your language.

**The solution**: An AI assistant that answers 80% of immigration questions instantly, and routes the complex 20% to vetted attorneys — generating referral revenue in the process.

**The founder**: An immigrant building for his own community. Trust, privacy, and multilingual quality are non-negotiable from day one.

**Domains**: `migravio.ai` (primary) · `migravio.com` (redirects to .ai)
**Name etymology**: *migra* (migrate) + *vio* (via — Latin/Spanish for path) = migration path

---

## Tech Stack — Non-Negotiable

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS | SSR, SEO, performance |
| Hosting (web) | Vercel | Zero-config Next.js deployment |
| PWA | Yes — manifest + service worker | Mobile home screen install |
| AI Service | Python FastAPI | RAG pipeline, model routing, streaming |
| Hosting (API) | Railway or Render | Simple Python hosting |
| Auth + DB | Firebase (Auth + Firestore + Storage) | Founder has experience, fully managed |
| AI Gateway | OpenRouter (`openrouter.ai/api/v1`) | One key for all models, cost visibility |
| AI Models | `anthropic/claude-haiku-4-5` (simple) · `anthropic/claude-sonnet-4-5` (complex) | Via OpenRouter |
| Vector DB | Pinecone (starter/free tier) | RAG knowledge base |
| Payments | Stripe (web-only) | No App Store cut |
| Email | Resend | Free up to 3K/month |
| i18n | next-intl | Multilingual from day one |

**OpenRouter usage** — use the `openai` Python package pointed at OpenRouter:
```python
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
```

---

## The Product — All Phases

### Phase 1 — MVP (Build Now)
*Goal: demoable product in 7 days. A user signs up, completes onboarding, asks immigration questions, sees their dashboard, and hits a paywall.*

**Auth** — Email/password + Google OAuth via Firebase. Protected routes for all dashboard pages.

**Onboarding** — 3 screens: (1) language select (EN, ES, HI, ZH, TL), (2) visa type (H-1B, F-1/OPT, Family, Green Card, Other), (3) key dates (visa expiry, priority date). Saved to Firestore user profile.

**AI Chat** — Streaming responses via FastAPI SSE. Multilingual. Message history in Firestore. Free tier: 10 messages/month (server-side enforced). When AI detects complexity keywords (RFE, denial, removal, asylum, deportation, appeal), append an attorney referral card below the response.

**Case Dashboard** — Visa status card, countdown timer to expiry (green > 90 days, yellow 30–90, red < 30), AI-generated action checklist based on visa type + dates, recent chat sessions.

**Attorney Referral** — Triggered by escalation detection or manual "Talk to an Attorney" CTA. Shows attorney name, specialty, languages, states licensed. "Request intro" sends email via Resend to both parties. MVP: 3–5 hardcoded founding attorney partners. Referrals tracked in Firestore.

**Paywall** — Free (10 msgs/month, English only) · Pro $19/mo or $190/yr (unlimited, all 5 languages, full dashboard) · Premium $39/mo (Pro + family profiles, priority attorney). Stripe Checkout. Stripe webhook updates Firestore subscription status. Always gate server-side — never trust client state.

**Policy Alerts** — Manual Firestore-curated USCIS updates. Shown on dashboard filtered by user's visa type. Simple card: "This affects H-1B holders."

**RAG Knowledge Base** — Ingest into Pinecone: USCIS Policy Manual, form instructions (I-485, I-130, I-539, I-765, I-131, N-400), visa type overviews (H-1B, H-4, L-1, O-1, F-1, OPT, EB-1/2/3), DHS processing times, BLS prevailing wage data. Chunk at 512 tokens with 50-token overlap. Tag each chunk with `visa_type[]` metadata for filtered retrieval.

---

### Phase 2 — Growth (Know This, Don't Build Yet)
*Goal: B2B revenue stream and employer market penetration.*

- **B2B Employer Dashboard** — SMBs manage visa employees, track I-94 expirations, H-1B renewals. Pricing: $299/mo (up to 10 employees), $699/mo (up to 50 + HRIS integration)
- **HRIS Integrations** — Rippling, Gusto, Deel. Sync employee visa data automatically. Sold as marketplace add-on
- **Document Prep** — AI-assisted form filling (I-485, I-130, etc.) with attorney review before submission. Requires careful UPL compliance design
- **Automated Policy Alerts** — Replace manual Firestore curation with USCIS.gov scraper + AI summarization pipeline
- **Push Notifications** — Web Push API for deadline reminders, policy alerts, attorney responses
- **Premium Tier activation** — Family profiles (multiple visa holders in one account), bulk document management
- **Attorney Network Expansion** — Self-serve attorney onboarding portal, listing fee model ($200–500/mo), rev-share dashboard

---

### Phase 3 — Scale (Future Context Only)
*Goal: market leadership and defensible moats.*

- **White-Label for Law Firms** — Law firms license Migravio as their client-facing AI assistant. $1,499/mo enterprise tier
- **DOJ-Accredited Org Partnerships** — Free/discounted tier for RAICES, IRC, CLINIC. Distribution + grant funding access
- **Court-Adjacent Services** — Removal defense workflow support, asylum case preparation. Requires DOJ-accredited representative supervision
- **Native Mobile App** — React Native after Phase 2 validates demand
- **Cross-Visa Pathway Planning** — AI models that map a user's full multi-year journey (F-1 → OPT → H-1B → EB-2 → Green Card) with probability and timeline forecasting
- **Multilingual Expansion** — French (Haitian), Portuguese (Brazilian), Vietnamese, Korean, Arabic

---

## Business Model

### Revenue Streams
| Stream | Phase | Model |
|--------|-------|-------|
| Pro subscriptions | 1 | $19/mo or $190/yr per user |
| Premium subscriptions | 1 | $39/mo per user |
| Attorney referral fees | 1 | $150 per successful intro |
| B2B employer plans | 2 | $299–$699/mo per company |
| Attorney listing fees | 2 | $200–$500/mo per attorney |
| White-label licenses | 3 | $1,499/mo per law firm |

### Unit Economics (Pro Tier)
- AI cost: ~$1.20/user/month · Infrastructure: ~$0.40 · Stripe fees: ~$0.55
- **Total cost: ~$2.15 · Revenue: $19 · Gross margin: ~89%**
- AI cost must never exceed 15% of revenue — enforce via semantic caching + model routing

---

## Legal & Compliance — Always

- The AI provides **legal information**, never **legal advice**
- Every response touching a user's specific situation must include a soft disclaimer
- Removal, deportation, asylum, court proceedings → **always escalate to attorney, no exceptions**
- Footer on all pages: *"Migravio provides legal information, not legal advice. We are not a law firm."*
- Firestore security rules: users read/write only their own documents. Referrals are server-side write only
- Never log full chat messages to third-party analytics. No selling or sharing user data — ever

---

## Multilingual — Not An Afterthought

MVP languages: **English, Spanish, Hindi, Mandarin (Simplified), Tagalog**

- Use `next-intl` for all UI strings from day one
- AI responds in the user's selected language (enforced in system prompt)
- Attorney profiles tagged with `languages_spoken[]`
- No Google Translate for UI — proper human translations only

---

## AI Behavior Rules

- Respond in the user's language at all times
- Be warm, clear, and human — not a legal textbook
- Ground all answers in retrieved RAG context
- Never hallucinate legal facts — if uncertain, say so and suggest an attorney
- Escalate on keywords: denied, RFE, removal, deportation, asylum, appeal, NOID, court
- Short factual queries → `claude-haiku-4-5` via OpenRouter
- Complex / escalation queries → `claude-sonnet-4-5` via OpenRouter
- Cache repeated queries in Firestore (cosine similarity > 0.92, TTL 7 days)

---

## Environment Variables

```bash
# Frontend (apps/web/.env.local)
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
AI_SERVICE_URL=http://localhost:8000
FIREBASE_ADMIN_SERVICE_ACCOUNT=   # JSON string

# AI Service (apps/ai-service/.env)
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
PINECONE_API_KEY=
PINECONE_INDEX_NAME=immigration-docs
FIREBASE_ADMIN_SERVICE_ACCOUNT=   # JSON string
```

---

## Core Principles

1. **Trust first** — sensitive immigration data; privacy is non-negotiable
2. **Plain language** — knowledgeable friend, not a lawyer
3. **Mobile-first** — 375px minimum, every screen
4. **Multilingual from day one** — not Phase 2
5. **Complexity = revenue** — attorney referral is a feature, not a failure
6. **89% gross margin** — protect it with caching, routing, smart decisions
7. **Never hallucinate** — wrong immigration advice can destroy someone's life

---

*Product: Migravio · migravio.ai · migravio.com*
*Founder: Gibran · Build partner: Claude · Last updated: March 2026*
