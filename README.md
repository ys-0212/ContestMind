<div align="center">
  <img src="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/brain-circuit.svg" alt="ContestMind Logo" width="100" height="100">
  <h1 align="center">ContestMind</h1>
  <p align="center">
    <strong>Your AI-Powered Competitive Programming Coach 🧠⚡</strong>
  </p>
  <p align="center">
    <a href="#-features">Features</a> •
    <a href="#-system-architecture">Architecture</a> •
    <a href="#-getting-started">Setup</a> •
    <a href="#%EF%B8%8F-usage">Usage</a>
  </p>
</div>

---

## 📖 Introduction

**ContestMind** is not just another coding dashboard—it is an intelligent, personalized learning and reasoning platform built for competitive programmers. By integrating directly with Codeforces, ContestMind analyzes your past submissions, identifies cognitive blockers, and provides a highly contextual AI coach to help you break through your plateau.

Stop grinding randomly. Start practicing intelligently.

---

## ✨ Features

| Feature | Description | Icon |
| :--- | :--- | :---: |
| **Progressive Coaching** | Tag-based, step-by-step hints (Constraint Analysis, Key Observations) designed to guide you without spoiling the solution. | 🔓 |
| **AI Contextual Chat** | An AI coach that sees your code, runtime errors, and expected outputs in real-time to debug alongside you. | 💬 |
| **Smart Recommendations** | Personalized problem sets dynamically generated based on your Codeforces rating, comfort zone, and tag weaknesses. | 🎯 |
| **Holistic Analytics** | Deep insights into your performance, including rating trajectories, difficulty distributions, and cognitive blockers. | 📊 |
| **Integrated IDE Workspace** | An immersive split-pane workspace with built-in code execution, custom I/O testing, and seamless Codeforces integration. | 💻 |

---

## 🏗️ System Architecture

ContestMind is built using a modern, scalable, and fully decoupled architecture.

### **Frontend (Next.js 15)**
- **Framework**: Next.js App Router (React 19)
- **Styling**: Tailwind CSS v4, Framer Motion for micro-animations
- **State & Data Fetching**: SWR for intelligent, deduped client-side caching
- **UI Components**: Radix UI primitives, Lucide Icons, Recharts for analytics

### **Backend (FastAPI)**
- **Framework**: Python FastAPI
- **Database**: Supabase (PostgreSQL) for user histories and attempts
- **Vector DB**: ChromaDB for Retrieval-Augmented Generation (RAG) and semantic problem search
- **Integrations**: Codeforces API, external Code Execution Engines (Piston), LLM APIs

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

- **Node.js** (v18+ recommended)
- **Python** (v3.10+ recommended)
- **Git**
- **Supabase** account (or local instance) for database configuration
- An **LLM API Key** (e.g., Groq, OpenAI, Anthropic)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ContestMind.git
cd ContestMind
```

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your SUPABASE keys and LLM keys

# Run the backend server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

Open a new terminal window:

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env.local
# Ensure NEXT_PUBLIC_API_URL is pointing to your backend (http://localhost:8000/api/v1)

# Start the development server
npm run dev
```

---

## 🕹️ Usage

1. **Dashboard Overview**: Navigate to `http://localhost:3000`. Set your Codeforces handle in the settings.
2. **Review Analytics**: The coaching engine will analyze your Codeforces history and generate your personalized "Comfort Zone", identifying your weakest tags.
3. **Pick a Problem**: Navigate to the Problem Set or use the "Recommended Problems" widget.
4. **Enter the Workspace**:
   - Read the problem statement on the left pane.
   - Code your solution in the right pane.
   - If stuck, request **Progressive Hints** or ask the **AI Coach**.
   - Run your code against the scraped examples or custom I/O.
5. **Submit**: Once you've verified your logic locally, submit directly to Codeforces!

---

## 🤝 Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<div align="center">
  <sub>Built with ❤️ for Competitive Programmers.</sub>
</div>
