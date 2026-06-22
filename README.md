<div align="center">

<br/>

```
   ██████╗ ██████╗ ███╗   ██╗████████╗███████╗███████╗████████╗    ███╗   ███╗██╗███╗   ██╗██████╗
  ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝    ████╗ ████║██║████╗  ██║██╔══██╗
  ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ███████╗   ██║       ██╔████╔██║██║██╔██╗ ██║██║  ██║
  ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ╚════██║   ██║       ██║╚██╔╝██║██║██║╚██╗██║██║  ██║
  ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗███████║   ██║       ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝   ╚═╝       ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝
```

**An AI-powered competitive programming coach that knows your code, your weaknesses, and your next move.**

<br/>

[![Next.js](https://img.shields.io/badge/Next.js-16.2-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35?style=flat-square)](https://www.trychroma.com/)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=flat-square)](https://groq.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com/)
[![ML Ensemble](https://img.shields.io/badge/ML-XGB+LGB+MLP_Ensemble-FF6F00?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)

</div>

---

## What is ContestMind?

ContestMind is a full-stack AI coaching platform built for competitive programmers. It connects to your Codeforces account, analyzes your submission history, and acts as a live coach inside a professional coding workspace.

Unlike generic AI chat assistants, ContestMind knows **your specific context** at every moment — which problem you're solving, what your code looks like, what verdict you got, and what your historical weaknesses are. The AI doesn't just answer questions; it diagnoses why you got WA, pinpoints your tag blind spots, and recommends exactly the right problem to solve next.

**Built as an end-to-end AI engineering portfolio project:** data pipeline → embeddings → vector search → RAG → ML inference → LLM reasoning → full-stack UI.

---

## Features

### Coding Workspace
- **Monaco Editor IDE** — VS Code quality editor with syntax highlighting for C++ 20, Python 3, Java, and JavaScript. Includes auto-closing brackets/quotes, bracket pair colorization, code folding, Find/Replace, smart indentation, and Ctrl+Enter to run.
- **Multi-language Templates** — Competitive-programming-ready boilerplate per language (fast I/O, buffered reader, etc.) that auto-loads when switching languages.
- **Code Persistence** — Your code is saved to `localStorage` per problem per language with a 500ms debounce. Switching problems or closing the tab never loses your work.
- **Live Code Execution** — Runs your code via Wandbox API with a local subprocess fallback (`g++`/`python`/`javac`). Verdicts: Accepted, Wrong Answer, Compile Error, Runtime Error, TLE.
- **Output Comparison** — Paste an expected output and get an Accepted/Wrong Answer verdict. The example test cases auto-fill stdin when you open a problem.
- **Submit Workflow** — One-click submit: auto-copies your code to clipboard with a toast notification, then opens the Codeforces submit page.
- **Font Size and Word Wrap Controls** — Customizable editor settings saved per session.

### AI Coaching
- **3-Level Progressive Hints** — Structured hint system that scaffolds toward a solution without spoiling it:
  - **Hint 1 — Constraint Analysis**: Surfaces a critical constraint that rules out naive approaches. Mentions no algorithms.
  - **Hint 2 — Algorithmic Direction**: Names the specific technique (DP, Binary Search, Segment Tree, etc.) with the key mathematical insight.
  - **Hint 3 — Implementation Guide**: Numbered pseudocode steps and explicit warnings about common pitfalls.
- **RAG-Powered Hints** — When editorial text is available in the vector database, hints are grounded in the actual editorial. When not available, the LLM reasons from tags and rating.
- **AI Chat with Full Workspace Context** — The floating AI assistant automatically receives your problem, code, execution verdict, input, and output. Ask "why WA?" and it diagnoses your actual code against the actual test case.
- **Chat History Persistence** — Conversation context is stored in Supabase and retrieved per session.

### Intelligence & Analytics
- **Solve Probability Engine** — A trained XGBoost Stacking Ensemble (XGBoost + LightGBM + MLP meta-learner) predicts your probability of solving any given problem. Trained on 50,000 samples with AUC-ROC 0.9734 and 91.7% accuracy. The model uses 15 engineered features including Elo baseline, comfort zone distance, experience tier, and stretch-problem flag.
- **Personalized Recommendations** — The recommendation engine uses ML probability to filter candidates to the 35–85% solve-probability sweet spot (neither trivially easy nor impossibly hard). An LLM then writes a personalized coaching rationale for each recommendation referencing your specific weak tags and rating gap.
- **Holistic Analytics Dashboard** — Analyzes your full Codeforces submission history to surface tag distribution, difficulty heatmap, weakest and strongest tags, comfort zone, and an LLM-generated paragraph of deep coaching insights targeting your exact blind spots.
- **Contest Intelligence** — Analyzes your in-contest submissions to detect: the problem index where your speed drops off, your in-contest accuracy rate, your most-failed tags under pressure, and your recent rating trend.
- **Rating Trajectory** — Interactive area chart of your full rating history across all rated contests.
- **Problem of the Day** — Dynamically selected daily from problems in the 1300–1800 difficulty range, preferring problems with full statements.

### Problem Discovery
- **15,000+ Problems** — Full Codeforces problemset loaded from the API cache with titles, tags, and ratings.
- **Semantic Search** — Natural-language search ("shortest path on a grid") powered by ChromaDB and `sentence-transformers/all-MiniLM-L6-v2` embeddings. Falls back to client-side title/tag filtering.
- **Advanced Filters** — Filter by min/max rating and one or more algorithm tags simultaneously.
- **Full Statement Problems** — Problems with scraped HTML statements and parsed test cases show a BookOpen indicator.
- **Problem Rendering** — Math-rich problem statements render perfectly with KaTeX (Codeforces `$$$...$$$` format). Section headers, examples, and HTML markup are all handled.

### Platform
- **Settings & BYOK** — Bring Your Own API Key for Groq, OpenAI, Gemini, or Anthropic. Key is stored locally in the browser and passed to the backend in-memory only.
- **Upcoming Contests** — Displays the next scheduled Codeforces round and your last 10 rated contest results with rank and rating delta.
- **Rate Limiting** — Built-in IP-based rate limiter (60 req/min) and structured request logging with latency headers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser (Next.js 16)                        │
│  Monaco Editor  │  KaTeX Math  │  Recharts  │  SWR (5min–24h cache) │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ REST API (JSON)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI + Uvicorn (Python 3.10)                 │
│  Rate Limiter (60/min/IP)  │  CORS  │  Request Logging + Latency   │
│                                                                     │
│  16 Route Modules: problems, profiles, analytics, hints, chat,      │
│  recommendations, probability, retrieval, rag, execute, ...         │
└──────┬──────────┬──────────┬───────────┬──────────┬────────────────┘
       │          │          │           │          │
       ▼          ▼          ▼           ▼          ▼
  Codeforces  ChromaDB    Supabase    Groq LLM   ML Model
     API      (Vector     (PostgreSQL  (LLaMA    (XGB+LGB+MLP
  (Profile,    Search,     chat logs,  3.3 70B)   Ensemble)
   Rating,     RAG hints)  hint track)
   Submissions)
       │                              │
       ▼                              ▼
  Wandbox API                  BeautifulSoup4
  (Code Execution              (CF Problem
   → local fallback)            Scraper)
```

### Data Flow: Problem Workspace

```
User opens problem
    → SWR fetches /problems/{id}
    → ProblemService checks scraped JSONL (TYPE A: full statement)
    → Falls back to CF API cache (TYPE B: title/tags/rating only)
    → KaTeX renders $$$...$$ math server-side via katex.renderToString
    → Monaco loads template or saved localStorage code
    → ProbabilityService: ML ensemble predicts solve % → LLM adds narrative

User runs code
    → POST /execute/ with code + stdin + expected_output
    → Wandbox API (primary) → local subprocess (g++/python/javac) fallback
    → Whitespace-tolerant output comparison → Accepted / Wrong Answer verdict
    → Result injected into AI chat context automatically

User asks AI Coach
    → POST /chat/ask with full workspace snapshot
    → ChatService queries ChromaDB for relevant editorial context (top-3, distance < 1.6)
    → Builds structured prompt: problem + code + verdict + RAG context + history
    → Groq LLaMA 3.3 70B → streaming response → react-markdown + KaTeX renders reply
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend Framework** | Next.js 16.2 (App Router) + React 19 | SSR-safe routing, streaming, server components |
| **Styling** | Tailwind CSS v4 + tw-animate-css | Utility-first dark theme with custom CSS vars |
| **UI Components** | Radix UI + shadcn/ui | Accessible primitives (cards, badges, inputs) |
| **Code Editor** | Monaco Editor (@monaco-editor/react 4.7) | VS Code engine, SSR-safe via `dynamic()` |
| **Math Rendering** | KaTeX 0.17 | Server-side `$$$...$$$` → HTML rendering |
| **Chat Rendering** | react-markdown + remark-math + rehype-katex + react-syntax-highlighter | Markdown + math + code blocks with copy |
| **Charts** | Recharts 3.8 | Rating trajectory (AreaChart), difficulty heatmap (BarChart) |
| **Animations** | Framer Motion 12 | Toast, card entrance, layout transitions |
| **Data Fetching** | SWR 2.4 | Deduped caching (5min–24h per endpoint type) |
| **Backend Framework** | FastAPI 0.115 + Uvicorn | Async REST API, OpenAPI docs at `/api/v1/openapi.json` |
| **Vector Database** | ChromaDB (local persistent) | Semantic search + RAG editorial context |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | 384-dim problem embeddings |
| **LLM** | Groq → LLaMA 3.3 70B Versatile | Hints, coaching, recommendations, analytics |
| **ML Model** | XGBoost + LightGBM + MLP Stacking Ensemble | Solve probability prediction (AUC-ROC 0.9734) |
| **Database** | Supabase PostgreSQL | Chat history, hint tracking, user profiles |
| **Auth** | Supabase Auth (+ localStorage MVP fallback) | Handle-based CF identity |
| **Code Execution** | Wandbox API → local subprocess | C++/Python/Java/JavaScript execution |
| **Web Scraping** | BeautifulSoup4 + cloudscraper | CF problem statement + example extraction |
| **Config** | Pydantic Settings | Typed env vars with `.env` file support |

---

## AI System

### How Hints Work

The hint service implements a **strict pedagogical progression** across 3 levels. Each level has its own prompt with explicit negative constraints to prevent spoilers:

```
Level 1 — Constraint Analysis
  Rule: ONLY discuss input sizes, value ranges, time/memory limits
  Forbidden: Naming any algorithm, technique, or data structure
  Example output: "With n up to 2×10⁵, any O(n²) approach exceeds 10⁸ operations."

Level 2 — Algorithmic Direction
  Rule: Name the specific algorithm AND give the key mathematical insight
  Forbidden: Pseudocode, implementation steps, repeating Level 1 content
  Example output: "Binary search on the answer: for a given mid, verify feasibility in O(n log n)..."

Level 3 — Implementation Guide
  Rule: Numbered pseudocode steps + explicit pitfall warnings
  Forbidden: Complete compilable code, repeating earlier content
```

When the ChromaDB vector index contains the editorial for the problem being solved, the hint prompt is grounded in that editorial text (RAG). When not available, the LLM reasons purely from tags and rating — both paths produce structured, pedagogically correct output.

### How Recommendations Work

```
1. Fetch user profile → extract weak_tags, comfort_zone_min/max
2. Query all problems in [comfort_min - 400, comfort_max + 400] rating band (shuffled, up to 100)
3. Filter out already-solved problems (cross-referenced with CF API submission status)
4. Run ML ensemble on each candidate → P(solve)
5. Hard filter: keep only candidates where 35% ≤ P(solve) ≤ 85%
6. Sort by probability descending; select `count` evenly spaced (smooth difficulty curve)
7. Batch LLM call: generate a personalized 3-4 sentence coaching rationale per problem
   referencing the user's specific weak tags, rating gap, and predicted probability
```

### How Analytics Work

The analytics pipeline processes every Codeforces submission in the user's history:

- **Tag Distribution**: Count unique AC solves per tag, identify strong (top 3) and weak (bottom 3 with ≥5 attempts) tags
- **Unexplored Topics**: Standard CF algorithmic domains (DP, graphs, trees, etc.) with zero attempts
- **Comfort Zone**: Median of solved-problem ratings ± 100
- **Contest Intelligence**: In-contest submissions grouped by contest → accuracy rate, average problems solved, speed dropoff point (problem index where avg solve time jumps by >30 min), in-contest failure tags
- **LLM Synthesis**: All of the above is assembled into a structured prompt and the LLM generates 3 personalized coaching insights targeting the user's exact progression blockers

### Solve Probability Model

| Metric | Value |
|--------|-------|
| Architecture | XGBoost + LightGBM + MLP → Logistic Regression meta-learner |
| Training samples | 50,000 (40k train / 10k test) |
| Accuracy | 91.65% |
| AUC-ROC | **0.9734** |
| F1 Score | 0.8922 |
| Brier Score | 0.0593 |

Top features by importance: `is_stretch_problem` (36%), `elo_baseline` (35%), `rating_difference` (13%), `rating_ratio` (10%).

The Elo baseline feature encodes the classical chess-derived formula `1 / (1 + 10^(Δrating/400))` as a strong prior. The ML model learns corrections on top of this prior using experience-based features (total solved, contest maturity, comfort zone distance).

---

## Local Development

### Prerequisites

- **Node.js** 18+
- **Python** 3.10+
- **Git**
- A **Groq API key** (free tier available at [console.groq.com](https://console.groq.com))
- Optional: **Supabase** project for chat history and hint tracking

### 1. Clone

```bash
git clone https://github.com/your-username/ContestMind.git
cd ContestMind
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — at minimum set GROQ_API_KEY
```

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/api/v1/openapi.json`

### 3. Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install

# Optional: create .env.local for custom API URL
# The default points to http://localhost:8000/api/v1
```

Start the dev server:

```bash
npm run dev
```

Open `http://localhost:3000` and enter your Codeforces handle on the login page.

### 4. Seed the Vector Index (Optional)

To enable semantic search and RAG-powered hints, seed the ChromaDB collection:

```bash
cd backend
python -m app.scripts.seed_vectors
```

This processes problems from `data/processed/problems.jsonl` and embeds them using `all-MiniLM-L6-v2`. Without this step, hints fall back to tag-only mode and search uses client-side filtering only.

---

## Environment Variables

### Backend (`backend/.env`)

```env
# Application
ENVIRONMENT=development
LOGGING_LEVEL=INFO
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# LLM — Groq (required for hints, chat, analytics, recommendations)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq

# Supabase (optional — enables chat history and hint tracking)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key

# ChromaDB (local by default, no setup needed)
CHROMA_PERSIST_DIR=data/chroma
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

### Frontend (`frontend/.env.local`)

```env
# Optional — defaults to localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Project Structure

```
ContestMind/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── api.py                    # Router aggregator (all 16 route modules)
│   │   │   └── routes/
│   │   │       ├── problems.py           # /problems, /problems/available, /problems/{id}
│   │   │       ├── profiles.py           # /profiles/{handle}
│   │   │       ├── analytics.py          # /analytics/weaknesses
│   │   │       ├── hints.py              # /hints/, /hints/{handle}/{id}
│   │   │       ├── chat.py               # /chat/ask
│   │   │       ├── recommendations.py    # /recommendations/
│   │   │       ├── probability.py        # /probability/{handle}/{id}
│   │   │       ├── retrieval.py          # /retrieval/search (semantic)
│   │   │       ├── rag.py                # /rag/simplify (editorial simplification)
│   │   │       ├── execute.py            # /execute/ (Wandbox → local fallback)
│   │   │       ├── contest_intelligence.py # /contest-intelligence/{handle}
│   │   │       └── ...
│   │   ├── services/
│   │   │   ├── problem_service.py        # JSONL loader + CF API cache
│   │   │   ├── probability_service.py    # ML ensemble inference + Elo fallback
│   │   │   ├── hint_service.py           # 3-level prompt builder + RAG retrieval
│   │   │   ├── chat_service.py           # Workspace context assembly + LLM chat
│   │   │   ├── recommendation_service.py # ML-filtered + LLM-reasoned recs
│   │   │   ├── analytics_service.py      # CF submission analysis + LLM insights
│   │   │   ├── contest_intelligence_service.py # In-contest performance analysis
│   │   │   ├── retrieval_service.py      # ChromaDB semantic search
│   │   │   ├── rag_service.py            # RAG editorial simplification
│   │   │   ├── scraper_service.py        # BeautifulSoup CF HTML scraper
│   │   │   ├── vector_service.py         # ChromaDB CRUD + embedding
│   │   │   └── llm/
│   │   │       ├── factory.py            # LLM provider factory (Groq / Gemini)
│   │   │       └── groq_service.py       # Groq LLaMA inference
│   │   ├── ml_models/
│   │   │   ├── solve_prob_ensemble.joblib  # XGB+LGB+MLP stacking ensemble
│   │   │   ├── solve_prob_metrics.json     # Model evaluation metrics
│   │   │   └── solve_prob_scaler.joblib    # Legacy MLP scaler
│   │   ├── schemas/                      # Pydantic request/response models
│   │   ├── core/
│   │   │   ├── config.py                 # Pydantic Settings
│   │   │   └── utils.py                  # TTL cache decorator
│   │   ├── scripts/                      # Data pipeline: scrape, embed, seed
│   │   └── main.py                       # FastAPI app + rate limiter + CORS
│   ├── data/
│   │   ├── raw/codeforces/               # CF API problem cache (auto-populated)
│   │   ├── processed/problems.jsonl      # Scraped problems with full statements
│   │   └── chroma/                       # ChromaDB persistent vector store
│   └── requirements.txt
│
└── frontend/
    └── src/
        ├── app/
        │   ├── layout.js                 # KaTeX CSS import, Geist font
        │   ├── page.js                   # Landing page
        │   ├── login/page.js             # CF handle + email/password validation
        │   ├── dashboard/
        │   │   ├── page.js               # Analytics + recommendations + rating chart
        │   │   ├── problems/page.js       # Problem browser: search + filters + POTD
        │   │   ├── problem/[id]/page.js  # Full IDE workspace (Monaco + hints + chat)
        │   │   ├── contests/page.js       # Upcoming contest + past performance
        │   │   ├── settings/page.js       # Profile sync + BYOK LLM key
        │   │   └── layout.js             # Dashboard sidebar layout
        ├── components/
        │   └── ChatMessage.jsx            # react-markdown + KaTeX + syntax highlight
        ├── hooks/
        │   └── useAPI.js                 # SWR hooks for all 8 endpoints
        ├── lib/
        │   ├── api.js                    # apiClient with all backend methods
        │   └── supabase.js               # Supabase SSR client
        ├── globals.css                   # Tailwind v4 theme + problem-content styles
        └── middleware.js                 # Auth middleware
```

---

## Design Decisions

**Why Groq instead of OpenAI/Gemini?** Groq's LPU inference hardware delivers LLaMA 3.3 70B at ~400 tokens/second — making multi-LLM features (hint generation + recommendation reasoning + analytics in a single session) practical without noticeable latency. The BYOK settings page lets users swap to OpenAI, Gemini, or Anthropic if they prefer.

**Why ChromaDB instead of Pinecone/Weaviate?** Local-first: the entire vector store lives on disk at `data/chroma/`. No network dependency, no API key, zero cost. The `VectorService` wraps the client, so swapping to a managed service is a one-file change.

**Why SWR instead of React Query or server components?** SWR's per-key deduplication with long TTLs (24h for CF problemset, 5min for semantic search) maps directly to the update frequency of each data source. This eliminates redundant Codeforces API calls without a server-side cache layer.

**Why XGBoost Stacking Ensemble instead of a simpler model?** The Elo baseline already achieves ~80% accuracy alone. The stacking ensemble corrects for cases where Elo systematically under- or over-estimates: experienced users who plateaued, cold-start users with few contests, and stretch problems where psychological factors matter. The 15-feature design was motivated by EDA on CF submission data, not arbitrary complexity.

**Why Monaco Editor?** Competitive programmers expect VS Code features: multi-cursor, bracket matching, code folding, Find/Replace (Ctrl+H), keyboard shortcuts (Ctrl+Enter to run). Replacing the previous `<textarea>` with Monaco required SSR-safe dynamic import and a stale-closure fix for the run-code keyboard action via `useRef`.

**Why KaTeX instead of MathJax?** Codeforces problems use `$$$...$$$` as their math delimiter, which is incompatible with MathJax v2's standard `$...$` / `$$...$$` delimiters. MathJax was silently corrupting every math expression. KaTeX with a custom `$$$...$$$` regex replacement renders problem statements and editorials correctly in ~5ms.

---

## Roadmap

- [ ] Real Supabase Auth (currently localStorage handle only)
- [ ] Problem scraping on-demand: when a user opens an unscraped problem, trigger live CF HTML scrape + cache
- [ ] Full editorial indexing: run scraper across all problems, re-seed ChromaDB for RAG-powered hints at scale
- [ ] Virtual scroll for the 15k+ problem browser (currently capped at 250 displayed)
- [ ] Contest prep mode: given an upcoming round, generate a 7-day personalized practice plan
- [ ] Penalty-time analysis: calculate time penalty per problem type from in-contest submissions
- [ ] Rating prediction: project future rating based on recent trajectory and practice patterns

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Ensure the backend starts without errors: `uvicorn app.main:app --reload`
4. Ensure the frontend builds: `npm run build`
5. Open a pull request with a clear description of what changed and why

---

<div align="center">
  <sub>Built for competitive programmers, by a competitive programmer.</sub>
  <br/>
  <sub>If this helps you reach your next rating tier, give it a star.</sub>
</div>
