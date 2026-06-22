"use client"
import React, { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkMath from "remark-math"
import rehypeKatex from "rehype-katex"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism"
import { Copy, CheckCircle2 } from "lucide-react"

// ── Code block with copy button ───────────────────────────────────────────────

function CodeBlock({ className, children }) {
  const [copied, setCopied] = useState(false)
  const lang = /language-(\w+)/.exec(className || "")?.[1] || ""
  const code = String(children).replace(/\n$/, "")

  const handleCopy = () => {
    navigator.clipboard?.writeText(code).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="my-2 rounded-lg overflow-hidden border border-[#1f1f1f] text-xs">
      <div className="flex items-center justify-between bg-[#0c0c0c] px-3 py-1.5 border-b border-[#1f1f1f]">
        <span className="text-[10px] text-[#a1a1aa] font-mono uppercase tracking-wider">
          {lang || "code"}
        </span>
        <button
          onClick={handleCopy}
          className="text-[10px] text-[#a1a1aa] hover:text-[#e5e2e1] flex items-center gap-1 transition-colors"
        >
          {copied
            ? <><CheckCircle2 className="h-3 w-3 text-[#10b981]" />Copied</>
            : <><Copy className="h-3 w-3" />Copy</>}
        </button>
      </div>
      {lang
        ? (
          <SyntaxHighlighter
            language={lang}
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              padding: "0.75rem",
              background: "#0c0c0c",
              fontSize: "12px",
              lineHeight: "1.5",
            }}
            codeTagProps={{ style: { fontFamily: "'JetBrains Mono', monospace" } }}
            PreTag="div"
          >
            {code}
          </SyntaxHighlighter>
        )
        : (
          <pre className="bg-[#0c0c0c] p-3 text-[#e5e2e1] font-mono text-[12px] overflow-x-auto leading-relaxed">
            {code}
          </pre>
        )}
    </div>
  )
}

// ── Inline code ───────────────────────────────────────────────────────────────

function InlineCode({ children }) {
  return (
    <code className="bg-[#1f1f1f] text-[#4cd7f6] px-1 py-0.5 rounded text-[11px] font-mono">
      {children}
    </code>
  )
}

// ── Markdown component map ────────────────────────────────────────────────────

const mdComponents = {
  // Code: detect inline vs block by whether children has a newline
  code({ className, children, ...props }) {
    const content = String(children)
    const hasLanguage = /language-(\w+)/.test(className || "")
    const isBlock = hasLanguage || content.includes("\n")
    if (!isBlock) return <InlineCode>{children}</InlineCode>
    return <CodeBlock className={className}>{children}</CodeBlock>
  },
  p: ({ children }) => (
    <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>
  ),
  li: ({ children }) => <li>{children}</li>,
  h1: ({ children }) => (
    <h1 className="text-sm font-bold text-[#e5e2e1] mb-1 mt-3 pb-1 border-b border-[#1f1f1f]">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-xs font-bold text-[#e5e2e1] mb-1 mt-2">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-xs font-semibold text-[#10b981] mb-0.5 mt-1.5">{children}</h3>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-[#3c4a42] pl-2 my-1 text-[#a1a1aa] italic">
      {children}
    </blockquote>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-[#e5e2e1]">{children}</strong>
  ),
  em: ({ children }) => (
    <em className="italic text-[#bbcabf]">{children}</em>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-[#4cd7f6] underline underline-offset-2 hover:text-[#7de9ff] transition-colors"
    >
      {children}
    </a>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto my-2">
      <table className="text-xs border-collapse min-w-full">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-[#3c4a42] px-2 py-1 text-[#10b981] font-semibold bg-[#0c0c0c] text-left">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border border-[#1f1f1f] px-2 py-1">{children}</td>
  ),
  hr: () => <hr className="border-[#1f1f1f] my-2" />,
  pre: ({ children }) => <>{children}</>,
}

// ── ChatMessage ───────────────────────────────────────────────────────────────

export function ChatMessage({ role, content }) {
  if (role === "user") {
    return (
      <div className="bg-[#10b981] text-[#002113] rounded-lg rounded-tr-none p-3 text-sm max-w-[85%] ml-auto leading-relaxed">
        {content}
      </div>
    )
  }

  return (
    <div className="bg-[#1a1a1a] border border-[#1f1f1f] rounded-lg rounded-tl-none px-3 pt-2.5 pb-1.5 text-sm text-[#e5e2e1] max-w-[95%] overflow-hidden">
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={mdComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
