"use client"
import React, { useState, useEffect, useRef, useCallback, useMemo } from "react"
import dynamic from "next/dynamic"
import katex from "katex"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Play, Send, ChevronRight, Lock, BrainCircuit, Terminal, ArrowLeft,
  Loader2, CheckCircle2, XCircle, AlertTriangle, ExternalLink, Copy,
  WrapText, FileCode, AlignLeft, Upload,
} from "lucide-react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { apiClient } from "@/lib/api"
import { useProblem, useProbability } from "@/hooks/useAPI"
import { ChatMessage } from "@/components/ChatMessage"

// ── Monaco Editor (SSR-safe) ──────────────────────────────────────────────────

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false })

// ── Language config ───────────────────────────────────────────────────────────

const LANGUAGES = {
  "C++ 20": {
    id: "cpp",
    monacoId: "cpp",
    ext: "cpp",
    template: `#include <bits/stdc++.h>
using namespace std;

void solve() {
    // your code here
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    int t;
    cin >> t;
    while (t--) solve();
    return 0;
}`,
  },
  "Python 3": {
    id: "python",
    monacoId: "python",
    ext: "py",
    template: `import sys
input = sys.stdin.readline

def solve():
    pass

t = int(input())
for _ in range(t):
    solve()`,
  },
  "Java": {
    id: "java",
    monacoId: "java",
    ext: "java",
    template: `import java.util.*;
import java.io.*;

public class Main {
    static BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
    static PrintWriter out = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out)));

    public static void main(String[] args) throws IOException {
        int t = Integer.parseInt(br.readLine().trim());
        while (t-- > 0) {
            solve();
        }
        out.flush();
    }

    static void solve() throws IOException {
        // your code here
    }
}`,
  },
  "JavaScript": {
    id: "javascript",
    monacoId: "javascript",
    ext: "js",
    template: `const lines = require('fs').readFileSync('/dev/stdin','utf8').trim().split('\\n');
let idx = 0;
const input = () => lines[idx++];

const t = parseInt(input());
for (let i = 0; i < t; i++) {
    solve();
}

function solve() {
    // your code here
}`,
  },
}

const HINT_TITLES = ["Constraint Analysis", "Key Observation", "Implementation Detail"]

// ── Verdict config ────────────────────────────────────────────────────────────

const VERDICT = {
  accepted:      { label: "Accepted",            color: "text-[#10b981]", bg: "bg-[#10b981]/10 border-[#10b981]/30" },
  wrong_answer:  { label: "Wrong Answer",         color: "text-[#ef4444]", bg: "bg-[#ef4444]/10 border-[#ef4444]/30" },
  compile_error: { label: "Compile Error",        color: "text-[#f59e0b]", bg: "bg-[#f59e0b]/10 border-[#f59e0b]/30" },
  runtime_error: { label: "Runtime Error",        color: "text-[#ef4444]", bg: "bg-[#ef4444]/10 border-[#ef4444]/30" },
  tle:           { label: "Time Limit Exceeded",  color: "text-[#f59e0b]", bg: "bg-[#f59e0b]/10 border-[#f59e0b]/30" },
  error:         { label: "Execution Error",      color: "text-[#ef4444]", bg: "bg-[#ef4444]/10 border-[#ef4444]/30" },
  ok:            { label: "Success",              color: "text-[#10b981]", bg: "bg-[#10b981]/10 border-[#10b981]/30" },
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function cfUrl(id) {
  const m = id?.match(/^(\d+)([A-Za-z][A-Za-z0-9]*)$/)
  return m
    ? `https://codeforces.com/problemset/problem/${m[1]}/${m[2].toUpperCase()}`
    : `https://codeforces.com/problemset`
}

function diffBadge(rating) {
  if (!rating) return "medium"
  if (rating < 1200) return "easy"
  if (rating < 1600) return "medium"
  if (rating < 2000) return "hard"
  return "expert"
}

function _isHtml(text) {
  return /<[a-z][\s\S]*>/i.test(text.substring(0, 500))
}

function renderCFContent(text) {
  if (!text) return ""
  let result = text

  if (!_isHtml(text)) {
    result = result
      .replace(/^time limit per test\s*\n.*(\n|$)/gim, "")
      .replace(/^memory limit per test\s*\n.*(\n|$)/gim, "")
      .replace(/^input\s*\nstandard input(\n|$)/gim, "")
      .replace(/^output\s*\nstandard output(\n|$)/gim, "")

    const sectionHeaders = ["Input", "Output", "Note", "Notes", "Examples", "Example", "Constraints"]
    sectionHeaders.forEach(h => {
      result = result.replace(
        new RegExp(`^(${h}):?\\s*$`, "gim"),
        `<span class="cf-section-header">$1</span>`,
      )
    })
  }

  result = result.replace(/\$\$\$([^]*?)\$\$\$/g, (match, inner) => {
    const latex = inner.trim()
    const displayMode = inner.includes("\n")
    try {
      return katex.renderToString(latex, { throwOnError: false, displayMode, output: "html", strict: false })
    } catch {
      return match
    }
  })

  return result
}

function splitStatement(problem) {
  if (!problem || !problem.statement) return { body: null, examples: [], timeLimit: "2 seconds", memoryLimit: "256 megabytes" }
  const examples = problem.examples || []
  let timeLimit = "2 seconds"
  let memoryLimit = "256 megabytes"
  const timeMatch = problem.statement.match(/time limit per test\s*\n(.*)/i)
  if (timeMatch) timeLimit = timeMatch[1].trim()
  const memMatch = problem.statement.match(/memory limit per test\s*\n(.*)/i)
  if (memMatch) memoryLimit = memMatch[1].trim()
  return { body: problem.statement, examples, timeLimit, memoryLimit }
}

// ── ContestMind Monaco theme (defined on editor mount) ────────────────────────

const CM_THEME_DEF = {
  base: "vs-dark",
  inherit: true,
  rules: [
    { token: "comment",       foreground: "6A9955", fontStyle: "italic" },
    { token: "keyword",       foreground: "569CD6" },
    { token: "keyword.control", foreground: "C586C0" },
    { token: "string",        foreground: "CE9178" },
    { token: "string.escape", foreground: "D7BA7D" },
    { token: "number",        foreground: "B5CEA8" },
    { token: "type",          foreground: "4EC9B0" },
    { token: "class",         foreground: "4EC9B0" },
    { token: "function",      foreground: "DCDCAA" },
    { token: "variable",      foreground: "9CDCFE" },
    { token: "constant",      foreground: "4FC1FF" },
    { token: "delimiter",     foreground: "D4D4D4" },
    { token: "operator",      foreground: "D4D4D4" },
  ],
  colors: {
    "editor.background":                   "#0c0c0c",
    "editor.foreground":                   "#e5e2e1",
    "editor.lineHighlightBackground":      "#141414",
    "editor.lineHighlightBorder":          "#00000000",
    "editor.selectionBackground":          "#1f3a2e",
    "editor.inactiveSelectionBackground":  "#1a2a22",
    "editor.selectionHighlightBackground": "#1a2a2240",
    "editorLineNumber.foreground":         "#3f3f46",
    "editorLineNumber.activeForeground":   "#a1a1aa",
    "editorCursor.foreground":             "#10b981",
    "editorCursor.background":             "#0c0c0c",
    "editorIndentGuide.background1":       "#1f1f1f",
    "editorIndentGuide.activeBackground1": "#3c4a42",
    "editorBracketMatch.background":       "#3c4a4250",
    "editorBracketMatch.border":           "#3c4a42",
    "scrollbarSlider.background":          "#1f1f1f80",
    "scrollbarSlider.hoverBackground":     "#3c4a4260",
    "scrollbarSlider.activeBackground":    "#3c4a4280",
    "editorGutter.background":             "#0c0c0c",
    "editorWidget.background":             "#141414",
    "editorWidget.border":                 "#1f1f1f",
    "editorSuggestWidget.background":      "#141414",
    "editorSuggestWidget.border":          "#1f1f1f",
    "editorSuggestWidget.selectedBackground": "#1f1f1f",
    "input.background":                    "#0c0c0c",
    "input.border":                        "#1f1f1f",
    "focusBorder":                         "#10b98140",
    "list.hoverBackground":                "#141414",
    "list.activeSelectionBackground":      "#1f3a2e",
    "editorHoverWidget.background":        "#141414",
    "editorHoverWidget.border":            "#1f1f1f",
  },
}

// ── Toast component ───────────────────────────────────────────────────────────

function Toast({ message, type, visible }) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key="toast"
          initial={{ opacity: 0, y: 16, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 16, scale: 0.95 }}
          transition={{ duration: 0.18 }}
          className={`fixed bottom-24 left-1/2 -translate-x-1/2 z-[200] px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 shadow-2xl pointer-events-none ${
            type === "error"
              ? "bg-[#1a0a0a] border border-[#ef4444]/40 text-[#ef4444]"
              : "bg-[#0a1a12] border border-[#10b981]/40 text-[#10b981]"
          }`}
        >
          {type === "error"
            ? <XCircle className="h-4 w-4 shrink-0" />
            : <CheckCircle2 className="h-4 w-4 shrink-0" />}
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// ── Components ────────────────────────────────────────────────────────────────

function ExampleBlock({ example, index, onUse }) {
  const [copied, setCopied] = useState(false)
  const copy = (text) => {
    navigator.clipboard?.writeText(text).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div className="rounded-lg border border-[#1f1f1f] overflow-hidden mb-3 last:mb-0">
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#1a1a1a] border-b border-[#1f1f1f]">
        <span className="text-xs font-semibold text-[#a1a1aa] tracking-wider uppercase">Example {index + 1}</span>
        <div className="flex gap-1">
          <button
            onClick={() => copy(example.input)}
            className="text-[10px] px-2 py-0.5 rounded text-[#a1a1aa] hover:text-[#e5e2e1] hover:bg-[#2a2a2a] transition-colors"
          >
            {copied ? "Copied!" : "Copy input"}
          </button>
          <button
            onClick={() => onUse(example)}
            className="text-[10px] px-2 py-0.5 rounded text-[#4cd7f6] hover:bg-[#4cd7f6]/10 border border-[#4cd7f6]/30 transition-colors"
          >
            Use in IDE
          </button>
        </div>
      </div>
      <div className="grid grid-cols-2 divide-x divide-[#1f1f1f]">
        <div className="p-3">
          <div className="text-[10px] text-[#a1a1aa] mb-1 font-semibold uppercase tracking-wider">Input</div>
          <pre className="text-[#e5e2e1] font-mono text-xs whitespace-pre-wrap break-all leading-relaxed">{example.input || "(empty)"}</pre>
        </div>
        <div className="p-3">
          <div className="text-[10px] text-[#a1a1aa] mb-1 font-semibold uppercase tracking-wider">Output</div>
          <pre className="text-[#10b981] font-mono text-xs whitespace-pre-wrap break-all leading-relaxed">{example.output || "(empty)"}</pre>
        </div>
      </div>
    </div>
  )
}

function VerdictBadge({ status }) {
  const v = VERDICT[status] || VERDICT.ok
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded border ${v.color} ${v.bg}`}>
      {status === "accepted" && <CheckCircle2 className="h-3 w-3" />}
      {["wrong_answer", "runtime_error", "error"].includes(status) && <XCircle className="h-3 w-3" />}
      {["compile_error", "tle"].includes(status) && <AlertTriangle className="h-3 w-3" />}
      {v.label}
    </span>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ProblemView({ params }) {
  const router = useRouter()
  const { id } = React.use(params)

  const { problem, isLoading: loading } = useProblem(id)

  // ── Handle ─────────────────────────────────────────────────────────────────
  const [handle, setHandle] = useState("")
  useEffect(() => {
    if (typeof window !== "undefined") setHandle(localStorage.getItem("cf_handle") || "guest")
  }, [])

  const { probabilityData } = useProbability(
    handle && handle !== "guest" ? handle : null, id
  )

  // ── UI tabs ────────────────────────────────────────────────────────────────
  const [activeLeftTab,  setActiveLeftTab]  = useState("statement")
  const [activeRightTab, setActiveRightTab] = useState("input")

  // ── IDE state ──────────────────────────────────────────────────────────────
  const [language, setLanguage] = useState("C++ 20")
  const [code,     setCode]     = useState(LANGUAGES["C++ 20"].template)

  // ── Editor settings ────────────────────────────────────────────────────────
  const [fontSize,  setFontSize]  = useState(14)
  const [wordWrap,  setWordWrap]  = useState(false)
  const [autoCopy,  setAutoCopy]  = useState(true)

  // ── Toast ──────────────────────────────────────────────────────────────────
  const [toast, setToast] = useState({ visible: false, message: "", type: "success" })
  const toastTimer = useRef(null)

  const showToast = useCallback((message, type = "success", ms = 2800) => {
    clearTimeout(toastTimer.current)
    setToast({ visible: true, message, type })
    toastTimer.current = setTimeout(() => setToast(t => ({ ...t, visible: false })), ms)
  }, [])

  // ── Monaco refs ────────────────────────────────────────────────────────────
  const editorRef    = useRef(null)
  const monacoRef    = useRef(null)
  const handleRunRef = useRef(null)  // prevents stale closure in Monaco keybinding

  // ── Examples ───────────────────────────────────────────────────────────────
  const [examples,        setExamples]        = useState([])
  const [selectedExample, setSelectedExample] = useState(0)
  const [customInput,     setCustomInput]      = useState("")
  const [expectedOutput,  setExpectedOutput]   = useState("")

  // ── Execution ──────────────────────────────────────────────────────────────
  const [runResult, setRunResult] = useState(null)
  const [isRunning, setIsRunning] = useState(false)

  // ── Hints ──────────────────────────────────────────────────────────────────
  const [hints,         setHints]         = useState([null, null, null])
  const [hintLoading,   setHintLoading]   = useState([false, false, false])
  const [hintsRevealed, setHintsRevealed] = useState(0)

  // ── Chat ───────────────────────────────────────────────────────────────────
  const [isChatOpen,    setIsChatOpen]    = useState(false)
  const [chatMessage,   setChatMessage]   = useState("")
  const [chatHistory,   setChatHistory]   = useState([
    { role: "assistant", content: "I'm here to help! Ask me about TLE, WA, or paste your error." }
  ])
  const [isChatLoading, setIsChatLoading] = useState(false)
  const chatEndRef     = useRef(null)
  const greetingSetRef = useRef(false)
  const saveTimer      = useRef(null)

  // ── localStorage: load code per problem + language ─────────────────────────
  useEffect(() => {
    if (!id || typeof window === "undefined") return
    const key = `cm_code_${id}_${LANGUAGES[language].id}`
    const saved = localStorage.getItem(key)
    const initial = saved ?? LANGUAGES[language].template
    setCode(initial)
    // If Monaco is already mounted, update its value directly to avoid cursor reset
    if (editorRef.current) {
      const model = editorRef.current.getModel()
      if (model && model.getValue() !== initial) model.setValue(initial)
    }
  }, [id, language])

  // ── localStorage: save code on change (debounced 500ms) ───────────────────
  useEffect(() => {
    if (!id || typeof window === "undefined") return
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => {
      localStorage.setItem(`cm_code_${id}_${LANGUAGES[language].id}`, code)
    }, 500)
    return () => clearTimeout(saveTimer.current)
  }, [code, id, language])

  // ── Auto-fill examples when problem loads ──────────────────────────────────
  useEffect(() => {
    if (problem) {
      const { examples: ex } = splitStatement(problem)
      setExamples(ex)
      if (ex.length > 0) {
        setCustomInput(ex[0].input)
        setExpectedOutput(ex[0].output)
        setSelectedExample(0)
      }
    }
  }, [problem])

  // ── Greeting ───────────────────────────────────────────────────────────────
  useEffect(() => {
    if (problem?.title && !greetingSetRef.current) {
      greetingSetRef.current = true
      const tagHint = problem.tags?.length ? ` (${problem.tags.slice(0, 2).join(", ")})` : ""
      setChatHistory([{
        role: "assistant",
        content: `I'm your AI coach for **"${problem.title}"**${tagHint}. I can see your code and run results in real time — ask me about your approach, a WA, or any implementation question!`,
      }])
    }
  }, [problem?.title])

  // ── Chat scroll ────────────────────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [chatHistory])

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleLanguageChange = useCallback((newLang) => {
    const prevTemplate = LANGUAGES[language]?.template
    if (code === prevTemplate || !code.trim()) {
      // Don't ask — just switch template (localStorage will load saved code)
    }
    setLanguage(newLang)
    // localStorage effect will fire and load saved/template code for new language
  }, [language, code])

  const handleUseExample = useCallback((ex, idx) => {
    setCustomInput(ex.input)
    setExpectedOutput(ex.output)
    setSelectedExample(idx)
    setActiveRightTab("input")
  }, [])

  const handleRevealHint = async (idx) => {
    const hintId = idx + 1
    if (hintId > hintsRevealed + 1) return
    if (hints[idx]) { setHintsRevealed(hintId); return }
    setHintLoading(prev => { const n = [...prev]; n[idx] = true; return n })
    try {
      const prevHints = hints.slice(0, idx).filter(v => v && !v.startsWith("Hint unavailable"))
      const data = await apiClient.getHints(id, hintId, prevHints)
      setHints(prev => { const n = [...prev]; n[idx] = data.hint_text; return n })
      setHintsRevealed(hintId)
      if (handle && handle !== "guest") {
        apiClient.post("/hints/", { handle, problem_id: id, hint_level: hintId }).catch(() => {})
      }
    } catch {
      setHints(prev => { const n = [...prev]; n[idx] = "Hint unavailable — try again."; return n })
      setHintsRevealed(hintId)
    } finally {
      setHintLoading(prev => { const n = [...prev]; n[idx] = false; return n })
    }
  }

  const handleRun = useCallback(async () => {
    if (isRunning) return
    setIsRunning(true)
    setRunResult(null)
    setActiveRightTab("output")
    try {
      const result = await apiClient.executeCode({
        code,
        language: LANGUAGES[language].id,
        stdin: customInput,
        expected_output: expectedOutput || undefined,
      })
      setRunResult(result)
    } catch (e) {
      setRunResult({ stdout: "", stderr: `Execution Error: ${e.message}\n\n(Try again in 30 seconds!)`, exit_code: 1, status: "error" })
    } finally {
      setIsRunning(false)
    }
  }, [isRunning, code, language, customInput, expectedOutput])

  // Keep ref fresh so Monaco keybinding always calls current handleRun
  handleRunRef.current = handleRun

  const handleFormat = useCallback(() => {
    editorRef.current?.getAction("editor.action.formatDocument")?.run()
  }, [])

  const handleSubmit = useCallback(async () => {
    const url = cfUrl(id)
    if (autoCopy) {
      try {
        await navigator.clipboard.writeText(code)
        showToast("Code copied to clipboard — paste it on Codeforces!", "success")
      } catch {
        showToast("Could not copy code. Opening Codeforces anyway.", "error")
      }
    }
    window.open(url, "_blank", "noopener,noreferrer")
  }, [id, code, autoCopy, showToast])

  const handleSendChat = async () => {
    if (!chatMessage.trim()) return
    const history = [...chatHistory, { role: "user", content: chatMessage }]
    setChatHistory(history)
    setChatMessage("")
    setIsChatLoading(true)
    try {
      const h = typeof window !== "undefined" ? (localStorage.getItem("cf_handle") || "guest") : "guest"
      const resp = await apiClient.post("/chat/ask", {
        query: chatMessage,
        handle: h,
        problem_id: id,
        problem_title: problem?.title ?? null,
        problem_tags: problem?.tags ?? null,
        problem_rating: problem?.rating ?? null,
        problem_statement: statementBody ? statementBody.slice(0, 5000) : null,
        hints: hints.filter(h => h && !h.startsWith("Hint unavailable")).join("\n\n"),
        editorial: problem?.editorial ? problem.editorial.slice(0, 5000) : null,
        user_code: code ? code.slice(0, 2000) : null,
        run_status: runResult?.status ?? null,
        run_stdout: runResult?.stdout ? runResult.stdout.slice(0, 500) : null,
        run_stderr: runResult?.stderr ? runResult.stderr.slice(0, 500) : null,
        stdin_used: customInput ? customInput.slice(0, 200) : null,
        expected_output: expectedOutput ? expectedOutput.slice(0, 200) : null,
      })
      setChatHistory([...history, { role: "assistant", content: resp.response_text || "Sorry, I couldn't respond." }])
    } catch {
      setChatHistory([...history, { role: "assistant", content: "Connection issue — try again." }])
    } finally {
      setIsChatLoading(false)
    }
  }

  // ── Derived ────────────────────────────────────────────────────────────────

  const probabilityPct = probabilityData?.probability_percent ?? null
  const { body: statementBody, examples: parsedExamples, timeLimit, memoryLimit } = problem?.statement
    ? splitStatement(problem)
    : { body: null, examples: [], timeLimit: "2 seconds", memoryLimit: "256 megabytes" }

  const renderedStatement = useMemo(() => renderCFContent(statementBody), [statementBody])
  const renderedEditorial = useMemo(() => renderCFContent(problem?.editorial), [problem?.editorial])

  const hasStatement = Boolean(problem?.statement)

  // ── Loading ────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center text-[#4cd7f6]">
          <Loader2 className="h-10 w-10 animate-spin mb-4" />
          <p className="font-semibold text-sm tracking-wider uppercase">Loading Workspace…</p>
        </div>
      </div>
    )
  }

  if (!problem) {
    return (
      <div className="flex h-full items-center justify-center text-[#a1a1aa] flex-col gap-4">
        <XCircle className="h-10 w-10 text-[#3c4a42]" />
        <p>Problem not found.</p>
        <Button variant="outline" size="sm" onClick={() => router.back()}>Go back</Button>
      </div>
    )
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-[calc(100vh-6rem)] w-full gap-4 pb-4">

      {/* ==================== LEFT PANE ==================== */}
      <div className="flex w-1/2 flex-col gap-4 h-full min-w-0">

        {/* Problem header + tabs */}
        <div className="flex h-[62%] flex-col rounded-lg border border-[#1f1f1f] bg-[#141414] overflow-hidden">
          <div className="flex items-center justify-between border-b border-[#1f1f1f] bg-[#1a1a1a] shrink-0 flex-wrap gap-y-1">
            <div className="flex items-center">
              <button onClick={() => router.back()} className="px-4 py-3 text-[#a1a1aa] hover:text-white transition-colors border-r border-[#1f1f1f]">
                <ArrowLeft className="h-4 w-4" />
              </button>
              {["statement", "editorial"].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveLeftTab(tab)}
                  className={`px-4 py-3 text-sm font-medium capitalize border-b-2 transition-colors ${activeLeftTab === tab ? "border-[#10b981] text-[#10b981]" : "border-transparent text-[#a1a1aa] hover:text-[#e5e2e1]"}`}
                >
                  {tab}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 pr-3">
              <Badge variant={diffBadge(problem.rating)}>{problem.rating ?? "N/A"}</Badge>
              <a href={cfUrl(id)} target="_blank" rel="noopener" className="text-[#a1a1aa] hover:text-[#4cd7f6] transition-colors">
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>

          <div className="flex-1 overflow-auto p-5 custom-scrollbar">
            {activeLeftTab === "statement" && (
              <>
                <div className="mb-4 pb-4 border-b border-[#1f1f1f]">
                  <h2 className="font-bold text-xl text-[#e5e2e1] mb-2">
                    {problem.problem_id}. {problem.title}
                  </h2>
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {problem.tags?.map(tag => (
                      <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                    ))}
                  </div>
                  <div className="flex gap-6 text-xs font-mono text-[#a1a1aa]">
                    <span>time: <span className="text-[#e5e2e1]">{timeLimit}</span></span>
                    <span>mem: <span className="text-[#e5e2e1]">{memoryLimit}</span></span>
                  </div>
                </div>

                {hasStatement ? (
                  <div
                    className="text-sm text-[#e5e2e1] leading-relaxed problem-content whitespace-pre-wrap"
                    dangerouslySetInnerHTML={{ __html: renderedStatement }}
                  />
                ) : (
                  <div className="rounded-lg border border-[#1f1f1f] bg-[#0c0c0c] p-5">
                    <div className="flex items-start gap-3 mb-4">
                      <ExternalLink className="h-4 w-4 text-[#4cd7f6] mt-0.5 shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-[#e5e2e1] mb-1">Statement not available locally</p>
                        <p className="text-xs text-[#a1a1aa] leading-relaxed">
                          This problem hasn't been scraped yet. View the full statement on Codeforces, then use the IDE and AI coach below.
                        </p>
                      </div>
                    </div>
                    <a href={cfUrl(id)} target="_blank" rel="noopener">
                      <Button size="sm" className="bg-[#1f1f1f] hover:bg-[#2a2a2a] border border-[#3c4a42] text-[#e5e2e1]">
                        <ExternalLink className="h-3.5 w-3.5 mr-1.5" />Open on Codeforces ↗
                      </Button>
                    </a>
                    <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                      {[["IDE", "Write & run code"], ["Hints", "Tag-based coaching"], ["AI Chat", "Ask the AI coach"]].map(([title, desc]) => (
                        <div key={title} className="rounded border border-[#1f1f1f] p-2">
                          <div className="text-xs font-semibold text-[#10b981] mb-0.5">{title}</div>
                          <div className="text-[10px] text-[#52525b]">{desc}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {parsedExamples.length > 0 && (
                  <div className="mt-6">
                    <div className="text-xs font-semibold text-[#a1a1aa] uppercase tracking-wider mb-3">Examples</div>
                    {parsedExamples.map((ex, i) => (
                      <ExampleBlock key={i} example={ex} index={i} onUse={(e) => handleUseExample(e, i)} />
                    ))}
                  </div>
                )}
              </>
            )}

            {activeLeftTab === "editorial" && (
              problem.editorial ? (
                <div
                  className="text-sm text-[#e5e2e1] problem-content whitespace-pre-wrap leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: renderedEditorial }}
                />
              ) : (
                <span className="text-[#a1a1aa]">No editorial available for this problem.</span>
              )
            )}
          </div>
        </div>

        {/* Bottom left: hints + probability */}
        <div className="flex flex-1 flex-col rounded-lg border border-[#1f1f1f] bg-[#141414] overflow-hidden min-h-0">
          <div className="flex items-center justify-between border-b border-[#1f1f1f] bg-[#1a1a1a]/70 px-4 py-2 shrink-0">
            <div className="flex items-center gap-2">
              <BrainCircuit className="h-4 w-4 text-[#4cd7f6]" />
              <span className="text-sm font-medium text-[#4cd7f6]">Progressive Coaching</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#a1a1aa]">Solve probability:</span>
              <div className="w-20 h-1.5 bg-[#1f1f1f] rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#3b82f6] to-[#4cd7f6] transition-all duration-700"
                  style={{ width: `${probabilityPct ?? 0}%` }}
                />
              </div>
              <span className="text-xs font-mono font-bold text-[#4cd7f6]">
                {probabilityPct != null ? `${probabilityPct.toFixed(0)}%` : "--%"}
              </span>
            </div>
          </div>

          <div className="flex-1 overflow-auto p-4 space-y-2">
            {HINT_TITLES.map((title, idx) => {
              const hintId   = idx + 1
              const revealed = hintsRevealed >= hintId
              const isNext   = hintsRevealed === idx
              const load     = hintLoading[idx]
              return (
                <div
                  key={hintId}
                  onClick={() => isNext && !load && handleRevealHint(idx)}
                  className={`rounded border transition-all p-3 text-sm flex flex-col relative overflow-hidden ${
                    revealed
                      ? "border-[#1f1f1f] bg-[#0c0c0c]"
                      : isNext
                        ? "border-[#3c4a42] bg-[#0c0c0c] hover:border-[#10b981] cursor-pointer group"
                        : "border-[#1f1f1f] bg-[#0c0c0c] opacity-40 pointer-events-none"
                  }`}
                >
                  {revealed ? (
                    <div>
                      <div className="flex items-center text-[#10b981] font-medium mb-1.5">
                        <ChevronRight className="h-4 w-4 mr-1 shrink-0" />
                        Hint {hintId}: {title}
                      </div>
                      <p className="text-[#bbcabf] pl-5 leading-relaxed text-xs">{hints[idx]}</p>
                    </div>
                  ) : load ? (
                    <div className="flex items-center text-[#a1a1aa] text-xs">
                      <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin shrink-0" />
                      Generating hint {hintId}…
                    </div>
                  ) : (
                    <div className="flex items-center justify-between w-full">
                      {isNext && (
                        <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-[#1f1f1f]/20 to-transparent" />
                      )}
                      <div className={`flex items-center text-xs ${isNext ? "text-[#a1a1aa]" : "text-[#3f3f46]"}`}>
                        <Lock className="h-3.5 w-3.5 mr-2 shrink-0" />
                        {isNext ? `Reveal Hint ${hintId}: ${title}` : `Hint ${hintId}: Locked`}
                      </div>
                      {isNext && (
                        <span className="text-[10px] opacity-0 group-hover:opacity-100 transition-opacity text-[#10b981] border border-[#10b981]/40 rounded px-1.5 py-0.5 relative z-10">
                          Click to reveal
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* ==================== RIGHT PANE ==================== */}
      <div className="flex w-1/2 flex-col gap-4 h-full min-w-0">

        {/* Monaco Editor card */}
        <div className="flex flex-1 flex-col rounded-lg border border-[#1f1f1f] bg-[#0c0c0c] overflow-hidden min-h-0">

          {/* ── Editor toolbar ── */}
          <div className="flex items-center justify-between border-b border-[#1f1f1f] bg-[#1a1a1a] px-3 py-1.5 shrink-0 gap-2 flex-wrap">

            {/* Left: file name + language selector */}
            <div className="flex items-center gap-2">
              <FileCode className="h-3.5 w-3.5 text-[#a1a1aa] shrink-0" />
              <span className="text-xs font-mono text-[#e5e2e1] shrink-0">
                solution.{LANGUAGES[language].ext}
              </span>
              <select
                value={language}
                onChange={e => handleLanguageChange(e.target.value)}
                className="bg-[#0c0c0c] border border-[#3c4a42] text-[10px] text-[#a1a1aa] rounded px-1.5 py-0.5 outline-none focus:border-[#10b981] cursor-pointer"
              >
                {Object.keys(LANGUAGES).map(l => <option key={l}>{l}</option>)}
              </select>
            </div>

            {/* Right: font, wrap, format, run, submit */}
            <div className="flex items-center gap-1">
              {/* Font size */}
              <div className="flex items-center bg-[#0c0c0c] border border-[#1f1f1f] rounded overflow-hidden">
                <button
                  onClick={() => setFontSize(s => Math.max(11, s - 1))}
                  className="px-1.5 py-0.5 text-[10px] text-[#a1a1aa] hover:text-white hover:bg-[#1f1f1f] transition-colors"
                  title="Decrease font size"
                >A-</button>
                <span className="text-[10px] text-[#52525b] px-1 min-w-[2.8rem] text-center tabular-nums">
                  {fontSize}px
                </span>
                <button
                  onClick={() => setFontSize(s => Math.min(22, s + 1))}
                  className="px-1.5 py-0.5 text-xs text-[#a1a1aa] hover:text-white hover:bg-[#1f1f1f] transition-colors"
                  title="Increase font size"
                >A+</button>
              </div>

              {/* Word wrap */}
              <button
                onClick={() => setWordWrap(w => !w)}
                title="Toggle word wrap"
                className={`p-1 rounded border transition-colors ${
                  wordWrap
                    ? "border-[#10b981]/40 text-[#10b981] bg-[#10b981]/10"
                    : "border-[#1f1f1f] text-[#52525b] hover:text-[#a1a1aa]"
                }`}
              >
                <WrapText className="h-3 w-3" />
              </button>

              {/* Format */}
              <button
                onClick={handleFormat}
                title="Format document (Shift+Alt+F)"
                className="p-1 rounded border border-[#1f1f1f] text-[#52525b] hover:text-[#a1a1aa] transition-colors"
              >
                <AlignLeft className="h-3 w-3" />
              </button>

              {/* Run */}
              <Button
                size="sm"
                className="h-6 text-[11px] px-2.5 bg-[#1f1f1f] hover:bg-[#2a2a2a] border-0 text-[#e5e2e1] gap-1"
                onClick={handleRun}
                disabled={isRunning}
                title="Run code (Ctrl+')"
              >
                {isRunning
                  ? <Loader2 className="h-2.5 w-2.5 animate-spin" />
                  : <Play className="h-2.5 w-2.5" />}
                Run
              </Button>

              {/* Submit */}
              <Button
                size="sm"
                className="h-6 text-[11px] px-2.5 bg-[#10b981] text-[#002113] hover:bg-[#059669] gap-1"
                onClick={handleSubmit}
                title={autoCopy ? "Copy code & open Codeforces" : "Open Codeforces"}
              >
                <Upload className="h-2.5 w-2.5" />
                Submit
              </Button>

              {/* Auto-copy toggle */}
              <button
                onClick={() => setAutoCopy(v => !v)}
                title={`Auto-copy on submit: ${autoCopy ? "ON" : "OFF"}`}
                className={`text-[9px] px-1 py-0.5 rounded border transition-colors ${
                  autoCopy
                    ? "border-[#10b981]/40 text-[#10b981]"
                    : "border-[#1f1f1f] text-[#52525b]"
                }`}
              >
                <Copy className="h-2.5 w-2.5" />
              </button>
            </div>
          </div>

          {/* ── Monaco Editor ── */}
          <div className="flex-1 min-h-0">
            <MonacoEditor
              height="100%"
              language={LANGUAGES[language].monacoId}
              value={code}
              onChange={(v) => setCode(v ?? "")}
              theme="contestmind-dark"
              options={{
                fontSize,
                fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace",
                fontLigatures: true,
                minimap:            { enabled: false },
                scrollbar: {
                  vertical:               "auto",
                  horizontal:             "auto",
                  useShadows:             false,
                  verticalScrollbarSize:  6,
                  horizontalScrollbarSize: 6,
                },
                lineNumbers:              "on",
                lineNumbersMinChars:      3,
                glyphMargin:              false,
                folding:                  true,
                lineDecorationsWidth:     4,
                renderLineHighlight:      "line",
                autoClosingBrackets:      "always",
                autoClosingQuotes:        "always",
                autoIndent:               "full",
                tabSize:                  4,
                insertSpaces:             true,
                wordWrap:                 wordWrap ? "on" : "off",
                scrollBeyondLastLine:     false,
                smoothScrolling:          true,
                cursorBlinking:           "phase",
                cursorSmoothCaretAnimation: "on",
                overviewRulerBorder:      false,
                overviewRulerLanes:       0,
                hideCursorInOverviewRuler: true,
                renderWhitespace:         "selection",
                bracketPairColorization:  { enabled: true },
                guides:                   { bracketPairs: true, indentation: true },
                suggest:                  { insertMode: "replace", showStatusBar: false },
                quickSuggestions:         { other: true, comments: false, strings: false },
                acceptSuggestionOnCommitCharacter: true,
                automaticLayout:          true,
                padding:                  { top: 12, bottom: 12 },
              }}
              loading={
                <div className="flex h-full items-center justify-center text-[#a1a1aa] text-xs gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-[#4cd7f6]" />
                  Loading editor…
                </div>
              }
              onMount={(editor, monaco) => {
                // Register + apply ContestMind theme
                monaco.editor.defineTheme("contestmind-dark", CM_THEME_DEF)
                monaco.editor.setTheme("contestmind-dark")

                // Ctrl+' → Run (mirrors old textarea shortcut)
                editor.addAction({
                  id:            "cm-run-code",
                  label:         "ContestMind: Run Code",
                  keybindings:   [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Quote],
                  contextMenuGroupId: "navigation",
                  run: () => handleRunRef.current?.(),
                })

                // Ctrl+Enter → Run (extra binding)
                editor.addAction({
                  id:          "cm-run-enter",
                  label:       "ContestMind: Run Code (Enter)",
                  keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
                  run: () => handleRunRef.current?.(),
                })

                editorRef.current  = editor
                monacoRef.current  = monaco
              }}
            />
          </div>
        </div>

        {/* Test I/O panel */}
        <div className="flex h-56 flex-col rounded-lg border border-[#1f1f1f] bg-[#141414] overflow-hidden shrink-0">
          <div className="flex items-center justify-between border-b border-[#1f1f1f] bg-[#1a1a1a] shrink-0">
            <div className="flex">
              {[{ key: "input", label: "Custom Input" }, { key: "output", label: "Output" }].map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setActiveRightTab(key)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    activeRightTab === key ? "border-[#10b981] text-[#10b981]" : "border-transparent text-[#a1a1aa] hover:text-[#e5e2e1]"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 pr-2">
              {examples.length > 1 && (
                <select
                  value={selectedExample}
                  onChange={e => {
                    const idx = Number(e.target.value)
                    handleUseExample(examples[idx], idx)
                  }}
                  className="bg-[#1f1f1f] border border-[#3c4a42] text-[10px] text-[#a1a1aa] rounded px-1.5 py-1 outline-none focus:border-[#10b981]"
                >
                  {examples.map((_, i) => <option key={i} value={i}>Example {i + 1}</option>)}
                </select>
              )}
              <Button size="sm" className="h-7 text-xs px-3 bg-[#1f1f1f] hover:bg-[#2a2a2a] border-0 text-[#e5e2e1]" onClick={handleRun} disabled={isRunning}>
                {isRunning ? <><Loader2 className="h-3 w-3 mr-1 animate-spin" />Running…</> : <><Play className="h-3 w-3 mr-1" />Run</>}
              </Button>
              <Button size="sm" className="h-7 text-xs px-3 bg-[#10b981] text-[#002113] hover:bg-[#059669]" onClick={handleSubmit}>
                Submit ↗
              </Button>
            </div>
          </div>

          <div className="flex-1 overflow-auto bg-[#0c0c0c]">
            {activeRightTab === "input" && (
              <div className="p-3 h-full flex flex-col gap-1">
                <div className="text-[10px] text-[#a1a1aa] uppercase tracking-wider font-semibold">stdin</div>
                <textarea
                  className="flex-1 w-full bg-[#141414] border border-[#1f1f1f] rounded text-[#e5e2e1] font-mono text-xs p-2 resize-none outline-none focus:border-[#3c4a42] leading-relaxed"
                  placeholder="Paste custom input here…"
                  value={customInput}
                  onChange={e => setCustomInput(e.target.value)}
                  spellCheck={false}
                />
                {expectedOutput && (
                  <div className="mt-1">
                    <div className="text-[10px] text-[#a1a1aa] uppercase tracking-wider font-semibold mb-1">expected output</div>
                    <pre className="text-[10px] font-mono text-[#3c4a42] bg-[#141414] border border-[#1f1f1f] rounded p-2 max-h-16 overflow-auto whitespace-pre-wrap">
                      {expectedOutput}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {activeRightTab === "output" && (
              <div className="p-3 space-y-2 font-mono text-xs">
                {isRunning && (
                  <div className="flex items-center gap-2 text-[#a1a1aa]">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />Executing…
                  </div>
                )}
                {runResult && !isRunning && (
                  <>
                    <div className="flex items-center gap-2 mb-2">
                      <VerdictBadge status={runResult.status} />
                      <span className="text-[#52525b] text-[10px]">exit {runResult.exit_code}</span>
                    </div>
                    {runResult.stdout && (
                      <div>
                        <div className="text-[10px] text-[#a1a1aa] uppercase tracking-wider font-semibold mb-1">stdout</div>
                        <pre className="text-[#10b981] whitespace-pre-wrap break-all">{runResult.stdout}</pre>
                      </div>
                    )}
                    {runResult.matched_expected === false && expectedOutput && (
                      <div className="mt-2">
                        <div className="text-[10px] text-[#a1a1aa] uppercase tracking-wider font-semibold mb-1">expected</div>
                        <pre className="text-[#4cd7f6] whitespace-pre-wrap break-all">{expectedOutput}</pre>
                      </div>
                    )}
                    {runResult.stderr && (
                      <div className="mt-2">
                        <div className="text-[10px] text-[#a1a1aa] uppercase tracking-wider font-semibold mb-1">
                          {runResult.status === "compile_error" ? "compiler output" : "stderr"}
                        </div>
                        <pre className="text-[#ef4444] whitespace-pre-wrap break-all">{runResult.stderr}</pre>
                      </div>
                    )}
                    {!runResult.stdout && !runResult.stderr && (
                      <div className="text-[#a1a1aa]">No output.</div>
                    )}
                  </>
                )}
                {!runResult && !isRunning && (
                  <div className="text-[#52525b] italic">Run your code to see output here.</div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ==================== FLOATING CHAT ==================== */}
      {isChatOpen && (
        <motion.div
          drag
          dragConstraints={{ left: typeof window !== "undefined" ? -window.innerWidth + 400 : -1000, top: typeof window !== "undefined" ? -window.innerHeight + 500 : -1000, right: 20, bottom: 20 }}
          dragElastic={0.1}
          dragMomentum={false}
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          className="fixed bottom-24 right-6 w-80 sm:w-[420px] h-[520px] bg-[#141414] border border-[#3c4a42] rounded-xl shadow-2xl flex flex-col overflow-hidden z-50 min-w-[300px] min-h-[300px] max-w-[90vw] max-h-[90vh] resize"
          style={{ position: "fixed" }}
        >
          <div className="flex items-center justify-between bg-[#1a1a1a] px-4 py-3 border-b border-[#1f1f1f] shrink-0 cursor-move active:cursor-grabbing">
            <div className="flex items-center gap-2">
              <BrainCircuit className="h-5 w-5 text-[#4cd7f6]" />
              <span className="font-semibold text-[#e5e2e1]">ContestMind AI</span>
            </div>
            <button onClick={() => setIsChatOpen(false)} className="text-[#a1a1aa] hover:text-[#e5e2e1] text-lg leading-none">✕</button>
          </div>

          <div className="flex-1 overflow-auto p-4 bg-[#0c0c0c] flex flex-col gap-3">
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex items-start ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                {msg.role === "assistant" && (
                  <div className="h-8 w-8 rounded-full bg-[#1f1f1f] border border-[#3c4a42] flex items-center justify-center mr-2.5 shrink-0 mt-0.5">
                    <BrainCircuit className="h-4 w-4 text-[#4cd7f6]" />
                  </div>
                )}
                <ChatMessage role={msg.role} content={msg.content} />
              </div>
            ))}
            {isChatLoading && (
              <div className="flex items-start">
                <div className="h-8 w-8 rounded-full bg-[#1f1f1f] border border-[#3c4a42] flex items-center justify-center mr-2.5 shrink-0 mt-0.5">
                  <BrainCircuit className="h-4 w-4 text-[#4cd7f6]" />
                </div>
                <div className="bg-[#1a1a1a] border border-[#1f1f1f] rounded-lg rounded-tl-none p-3 text-sm text-[#a1a1aa] flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />Thinking…
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="p-3 bg-[#0c0c0c] border-t border-[#1f1f1f] shrink-0">
            <div className="relative">
              <input
                type="text"
                value={chatMessage}
                onChange={e => setChatMessage(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !e.shiftKey && handleSendChat()}
                placeholder="Why did I get WA?"
                className="w-full bg-[#141414] border border-[#3c4a42] rounded-full py-2.5 pl-4 pr-10 text-sm text-[#e5e2e1] focus:outline-none focus:border-[#4cd7f6]"
              />
              <button
                onClick={handleSendChat}
                disabled={isChatLoading || !chatMessage.trim()}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded-full bg-[#4cd7f6] hover:bg-[#38bdf8] text-[#002113] transition-colors disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* ── Chat toggle button ── */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsChatOpen(v => !v)}
          className={`h-14 w-14 rounded-full flex items-center justify-center shadow-2xl transition-all hover:scale-105 active:scale-95 ${
            isChatOpen ? "bg-[#3c4a42] text-[#e5e2e1]" : "bg-[#10b981] text-[#002113] hover:bg-[#059669]"
          }`}
        >
          {isChatOpen ? <span className="text-xl leading-none">✕</span> : <BrainCircuit className="h-6 w-6" />}
        </button>
      </div>

      {/* ── Toast ── */}
      <Toast message={toast.message} type={toast.type} visible={toast.visible} />
    </div>
  )
}
