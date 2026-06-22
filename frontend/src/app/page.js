"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { BrainCircuit, ArrowRight, Code2, LineChart, Trophy, Lock, Zap, CheckCircle2, Star, Target } from "lucide-react"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"

export default function LandingPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState(0)

  const featureTabs = [
    { title: "Progressive Hints", icon: <Lock className="w-4 h-4" />, content: "Never read an editorial that spoils the entire solution. Our engine gives you strictly locked, progressive hints that nudge your logic exactly where you are stuck, preserving your 'Aha!' moment." },
    { title: "Weakness Radar", icon: <Target className="w-4 h-4" />, content: "We analyze thousands of your Codeforces submissions to detect structural weaknesses. Are you failing on DP because of state transitions or memory limits? We know, and we give you a tailored path." },
    { title: "IDE Workspace", icon: <Code2 className="w-4 h-4" />, content: "A high-density workspace built for the elite. Split panes for problem statement, AI coaching, test case execution, and your code. Say goodbye to scattered browser tabs." }
  ]

  return (
    <div className="min-h-screen bg-[#0c0c0c] text-[#e5e2e1] selection:bg-[#10b981] selection:text-[#002113] overflow-x-hidden">
      {/* HEADER */}
      <header className="fixed top-0 z-50 w-full border-b border-[#1f1f1f] bg-[#0c0c0c]/80 backdrop-blur-md">
        <div className="container mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center space-x-2">
            <BrainCircuit className="h-6 w-6 text-[#10b981]" />
            <span className="text-xl font-bold tracking-tight">ContestMind</span>
          </div>
          <nav className="hidden space-x-6 md:flex items-center text-sm font-medium text-[#a1a1aa]">
            <a href="#platform" className="hover:text-[#e5e2e1] transition-colors">Platform</a>
            <a href="#methodology" className="hover:text-[#e5e2e1] transition-colors">Methodology</a>
            <div className="h-4 w-px bg-[#1f1f1f]"></div>
            <Button variant="ghost" onClick={() => router.push('/login')} className="hover:bg-[#1f1f1f] hover:text-[#e5e2e1]">Sign In</Button>
            <Button onClick={() => router.push('/login')} className="bg-[#10b981] text-[#002113] hover:bg-[#059669]">Get Started</Button>
          </nav>
        </div>
      </header>

      {/* HERO SECTION */}
      <main className="flex flex-col items-center pt-32 pb-16 text-center px-4 relative">
        <div className="absolute inset-0 -z-10 h-[800px] w-full bg-[radial-gradient(#1f1f1f_1px,transparent_1px)] [background-size:24px_24px] opacity-40 mask-image:linear-gradient(to_bottom,white,transparent)"></div>
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#10b981] opacity-5 blur-[120px] rounded-full pointer-events-none"></div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center rounded-full border border-[#10b981]/30 bg-[#10b981]/10 px-3 py-1 text-xs font-semibold text-[#10b981] mb-8"
        >
          <span className="flex h-2 w-2 rounded-full bg-[#10b981] mr-2 animate-pulse shadow-[0_0_8px_#10b981]"></span>
          Algorithm Engine Active • v2.0
        </motion.div>
        
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="max-w-5xl text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tighter leading-[1.1] text-transparent bg-clip-text bg-gradient-to-b from-white via-[#e5e2e1] to-[#a1a1aa] mb-6"
        >
          Master Algorithmic <br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#10b981] via-[#34d399] to-[#4cd7f6] relative">
            Problem Solving
          </span>
        </motion.h1>
        
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="max-w-2xl text-lg md:text-xl text-[#a1a1aa] mb-10 leading-relaxed"
        >
          Stop reading editorials that ruin the solution. Sync your Codeforces profile and let our AI mentor guide you through your exact algorithmic weaknesses.
        </motion.p>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 w-full sm:w-auto"
        >
          <Button size="lg" className="h-14 text-base font-semibold group px-8 bg-[#10b981] hover:bg-[#059669] text-[#002113] w-full sm:w-auto shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all hover:shadow-[0_0_30px_rgba(16,185,129,0.5)]" onClick={() => router.push('/login')}>
            Start Free Training
            <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
          </Button>
          <Button size="lg" variant="outline" className="h-14 text-base font-semibold border-[#3c4a42] bg-[#141414]/50 backdrop-blur-sm hover:bg-[#1f1f1f] px-8 w-full sm:w-auto" onClick={() => document.getElementById('platform').scrollIntoView({ behavior: 'smooth' })}>
            Explore Platform
          </Button>
        </motion.div>

        {/* STATS STRIP */}
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-20 flex flex-wrap justify-center gap-8 md:gap-24 py-8 border-y border-[#1f1f1f]/50 w-full max-w-5xl"
        >
          <div className="flex flex-col items-center">
            <span className="text-3xl font-bold text-[#e5e2e1]">14,000+</span>
            <span className="text-xs text-[#a1a1aa] uppercase tracking-wider mt-1">Problems Indexed</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-3xl font-bold text-[#e5e2e1]">98%</span>
            <span className="text-xs text-[#a1a1aa] uppercase tracking-wider mt-1">Hint Accuracy</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-3xl font-bold text-[#e5e2e1]">+240</span>
            <span className="text-xs text-[#a1a1aa] uppercase tracking-wider mt-1">Avg Rating Gain</span>
          </div>
        </motion.div>
      </main>

      {/* PLATFORM SHOWCASE (Interactive Tabs) */}
      <section id="platform" className="py-24 bg-[#0c0c0c] relative">
        <div className="container mx-auto max-w-6xl px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Master every algorithm.</h2>
            <p className="text-[#a1a1aa] max-w-2xl mx-auto text-lg">We don't just give you the answer. We forge your brain to find it.</p>
          </div>

          <div className="flex flex-col lg:flex-row gap-12 items-center">
            {/* Interactive Tabs Menu */}
            <div className="w-full lg:w-1/3 flex flex-col space-y-4">
              {featureTabs.map((tab, idx) => (
                <div 
                  key={idx}
                  onClick={() => setActiveTab(idx)}
                  className={`p-6 rounded-xl cursor-pointer transition-all border ${activeTab === idx ? 'border-[#10b981] bg-[#141414] shadow-[0_0_20px_rgba(16,185,129,0.1)]' : 'border-[#1f1f1f] hover:border-[#3c4a42] hover:bg-[#141414]'}`}
                >
                  <div className={`flex items-center space-x-3 font-semibold text-lg mb-2 ${activeTab === idx ? 'text-[#10b981]' : 'text-[#e5e2e1]'}`}>
                    {tab.icon}
                    <span>{tab.title}</span>
                  </div>
                  <p className={`text-sm leading-relaxed ${activeTab === idx ? 'text-[#e5e2e1]' : 'text-[#a1a1aa]'}`}>
                    {tab.content}
                  </p>
                </div>
              ))}
            </div>

            {/* Mockup Preview Area */}
            <div className="w-full lg:w-2/3 h-[500px] rounded-xl border border-[#3c4a42] bg-[#141414] p-2 relative overflow-hidden shadow-2xl">
              <div className="absolute top-0 left-0 w-full h-8 bg-[#1a1a1a] flex items-center px-4 space-x-2 border-b border-[#1f1f1f]">
                <div className="w-3 h-3 rounded-full bg-[#ef4444]"></div>
                <div className="w-3 h-3 rounded-full bg-[#f59e0b]"></div>
                <div className="w-3 h-3 rounded-full bg-[#10b981]"></div>
              </div>
              
              <div className="mt-8 h-full w-full bg-[#0c0c0c] rounded border border-[#1f1f1f] flex flex-col items-center justify-center relative overflow-hidden p-8">
                {/* Dynamic content based on tab */}
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.4 }}
                  className="w-full max-w-md"
                >
                  {activeTab === 0 && (
                    <div className="space-y-3">
                      <div className="p-4 border border-[#1f1f1f] bg-[#141414] rounded-lg">
                        <div className="text-[#10b981] font-semibold text-sm mb-2 flex items-center"><CheckCircle2 className="w-4 h-4 mr-2"/>Hint 1: Constraint Analysis</div>
                        <p className="text-xs text-[#a1a1aa]">Notice N=1000. O(N^2) passes.</p>
                      </div>
                      <div className="p-4 border border-[#3c4a42] bg-gradient-to-r from-[#141414] to-[#0c0c0c] rounded-lg relative overflow-hidden">
                        <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-[#1f1f1f]/30 to-transparent"></div>
                        <div className="text-[#a1a1aa] font-semibold text-sm flex items-center"><Lock className="w-4 h-4 mr-2"/>Progressive Hint 2: Locked</div>
                      </div>
                      <div className="p-4 border border-[#1f1f1f] bg-[#0c0c0c] rounded-lg">
                        <div className="text-[#52525b] font-semibold text-sm flex items-center"><Lock className="w-4 h-4 mr-2"/>Progressive Hint 3: Locked</div>
                      </div>
                    </div>
                  )}
                  {activeTab === 1 && (
                    <div className="grid grid-cols-2 gap-4 w-full">
                      <div className="p-4 bg-linear-surface border border-[#ef4444]/30 rounded-lg text-center">
                        <div className="text-[#ef4444] font-bold text-xl mb-1">Critical Gap</div>
                        <div className="text-xs text-[#a1a1aa]">Dynamic Programming</div>
                      </div>
                      <div className="p-4 bg-linear-surface border border-[#10b981]/30 rounded-lg text-center">
                        <div className="text-[#10b981] font-bold text-xl mb-1">Strength</div>
                        <div className="text-xs text-[#a1a1aa]">Graph Theory</div>
                      </div>
                      <div className="col-span-2 p-4 bg-[#141414] border border-[#1f1f1f] rounded-lg mt-2">
                        <div className="h-2 w-full bg-[#1f1f1f] rounded-full overflow-hidden mb-2">
                          <div className="h-full bg-gradient-to-r from-[#f59e0b] to-[#ef4444] w-[45%]"></div>
                        </div>
                        <div className="text-[10px] text-[#a1a1aa] text-center uppercase tracking-widest">DP Solves (1600+)</div>
                      </div>
                    </div>
                  )}
                  {activeTab === 2 && (
                    <div className="flex h-48 border border-[#1f1f1f] rounded-lg overflow-hidden font-mono text-[10px] text-[#a1a1aa]">
                      <div className="w-1/2 border-r border-[#1f1f1f] p-3 bg-[#0c0c0c]">
                        <span className="text-[#3b82f6]">void</span> solve() {'{\n'}
                        &nbsp;&nbsp;<span className="text-[#10b981]">// your logic here</span>{'\n'}
                        {'}'}
                      </div>
                      <div className="w-1/2 flex flex-col">
                        <div className="h-1/2 border-b border-[#1f1f1f] p-3 bg-[#141414]">
                          Input: 4<br/>2<br/>Output: YES
                        </div>
                        <div className="h-1/2 p-3 bg-linear-surface flex items-center text-[#4cd7f6]">
                          <BrainCircuit className="w-3 h-3 mr-2" /> Ask AI...
                        </div>
                      </div>
                    </div>
                  )}
                </motion.div>
              </div>
            </div>
          </div>
        </div>
      </section>


      {/* CTA SECTION */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#10b981]/10 to-transparent"></div>
        <div className="container mx-auto max-w-4xl px-6 text-center relative z-10">
          <h2 className="text-4xl font-bold mb-6">Ready to break your rating plateau?</h2>
          <p className="text-[#a1a1aa] mb-10 text-lg">Join the beta today and sync your Codeforces profile in seconds.</p>
          <Button size="lg" className="h-14 px-10 bg-[#10b981] hover:bg-[#059669] text-[#002113] text-lg font-semibold" onClick={() => router.push('/login')}>
            Initialize Profile
          </Button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-[#1f1f1f] bg-[#0c0c0c] py-12">
        <div className="container mx-auto max-w-6xl px-6 flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center space-x-2 mb-4 md:mb-0">
            <BrainCircuit className="h-5 w-5 text-[#10b981]" />
            <span className="font-bold text-lg text-[#e5e2e1]">ContestMind</span>
          </div>
          
          <div className="flex space-x-6 text-sm text-[#a1a1aa]">
            <a href="#" className="hover:text-[#10b981] transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-[#10b981] transition-colors">Terms of Service</a>
          </div>
        </div>
        <div className="container mx-auto max-w-6xl px-6 mt-8 flex flex-col md:flex-row justify-between items-center text-xs text-[#a1a1aa]/60">
          <p>© 2026 ContestMind. All rights reserved.</p>
          <p className="mt-2 md:mt-0">Not affiliated with Codeforces.</p>
        </div>
      </footer>
    </div>
  )
}
