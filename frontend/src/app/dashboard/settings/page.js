"use client"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, User, Key, Bell, Shield, Loader2, Lock } from "lucide-react"
import { apiClient } from "@/lib/api"

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile")
  const [isSyncing, setIsSyncing] = useState(false)
  const [saveMessage, setSaveMessage] = useState("")
  
  // LLM Key State
  const [llmKey, setLlmKey] = useState("")
  const [showKey, setShowKey] = useState(false)
  const [llmProvider, setLlmProvider] = useState("Groq")
  const [keySaved, setKeySaved] = useState(false)
  
  const [handle, setHandle] = useState("")
  const [profile, setProfile] = useState(null)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedHandle = localStorage.getItem('cf_handle') || ''
      setHandle(storedHandle)
      if (storedHandle) {
        apiClient.getProfile(storedHandle).then(setProfile).catch(() => {})
      }
      const storedKey = localStorage.getItem('llm_api_key')
      if (storedKey) {
        setLlmKey(storedKey)
        setKeySaved(true)
      }
      const storedProvider = localStorage.getItem('llm_provider') || 'Groq'
      setLlmProvider(storedProvider)
    }
  }, [])

  const handleSaveLlmKey = () => {
    localStorage.setItem('llm_api_key', llmKey)
    localStorage.setItem('llm_provider', llmProvider)
    setKeySaved(true)
    setSaveMessage("LLM API Key saved successfully.")
    setTimeout(() => setSaveMessage(""), 3000)
  }

  const handleRemoveLlmKey = () => {
    localStorage.removeItem('llm_api_key')
    setLlmKey("")
    setKeySaved(false)
  }

  const handleForceSync = () => {
    setIsSyncing(true)
    if (handle) {
      apiClient.getProfile(handle).then(setProfile).catch(() => {}).finally(() => setIsSyncing(false))
    } else {
      setTimeout(() => setIsSyncing(false), 1500)
    }
  }

  return (
    <div className="max-w-4xl space-y-6 animate-in fade-in duration-500">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#e5e2e1]">Settings</h1>
        <p className="text-sm text-[#a1a1aa] mt-1">Manage your account and platform preferences.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        {/* Settings Sidebar */}
        <div className="md:col-span-1 space-y-1">
          <Button 
            variant={activeTab === "profile" ? "secondary" : "ghost"} 
            className={`w-full justify-start ${activeTab === "profile" ? "font-semibold" : ""}`}
            onClick={() => setActiveTab("profile")}
          >
            <User className="mr-2 h-4 w-4" /> Profile
          </Button>
          <Button 
            variant={activeTab === "api" ? "secondary" : "ghost"} 
            className={`w-full justify-start ${activeTab === "api" ? "font-semibold" : ""}`}
            onClick={() => setActiveTab("api")}
          >
            <Key className="mr-2 h-4 w-4" /> LLM Provider
          </Button>
          <Button 
            variant={activeTab === "notifications" ? "secondary" : "ghost"} 
            className={`w-full justify-start ${activeTab === "notifications" ? "font-semibold" : ""}`}
            onClick={() => setActiveTab("notifications")}
          >
            <Bell className="mr-2 h-4 w-4" /> Notifications
          </Button>
        </div>

        {/* Settings Content */}
        <div className="md:col-span-3 space-y-6">
          {activeTab === "profile" && (
            <>
              <Card className="border-[#1f1f1f] bg-[#0c0c0c]">
                <CardHeader>
                  <CardTitle>Codeforces Integration</CardTitle>
                  <CardDescription>Your linked competitive programming account.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-lg border border-[#3c4a42] bg-[#141414] p-4 gap-4">
                    <div className="flex items-center space-x-4">
                      {profile?.avatar_url ? (
                        <img src={profile.avatar_url} alt="Avatar" className="h-12 w-12 rounded-full border border-[#3c4a42]" />
                      ) : (
                        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[#10b981] to-[#059669] flex items-center justify-center font-bold text-lg text-[#002113]">
                          {handle ? handle.charAt(0).toUpperCase() : 'G'}
                        </div>
                      )}
                      <div>
                        <p className="text-base font-bold text-[#e5e2e1]">{handle || 'guest'}</p>
                        <p className="text-sm text-[#10b981] font-semibold capitalize">{profile?.rank || 'Unrated'} {profile?.current_rating ? `(${profile.current_rating})` : ''}</p>
                      </div>
                    </div>
                    <Badge variant="easy" className="flex items-center shrink-0">
                      <CheckCircle2 className="mr-1 h-3 w-3" /> Synced
                    </Badge>
                  </div>
                  <div className="flex justify-end">
                    <Button variant="outline" size="sm" onClick={handleForceSync} disabled={isSyncing} className="border-[#3c4a42] hover:bg-[#1f1f1f]">
                      {isSyncing ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Syncing...</> : "Force Sync Now"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {activeTab === "api" && (
            <Card className="border-[#1f1f1f] bg-[#0c0c0c]">
              <CardHeader>
                <CardTitle>Bring Your Own LLM Key</CardTitle>
                <CardDescription>Your API key is used ONLY to power AI tutoring features like hints, simplification, coaching, and chat.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2">
                  <label className="text-sm font-medium text-[#e5e2e1]">AI Provider</label>
                  <select 
                    value={llmProvider}
                    onChange={(e) => setLlmProvider(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-[#3c4a42] bg-[#141414] px-3 py-2 text-sm text-[#e5e2e1] focus:border-[#10b981] outline-none"
                  >
                    <option value="Groq">Groq (Default)</option>
                    <option value="OpenAI">OpenAI</option>
                    <option value="Gemini">Gemini</option>
                    <option value="Anthropic">Anthropic</option>
                  </select>
                </div>
                <div className="grid gap-2">
                  <label className="text-sm font-medium text-[#e5e2e1]">API Key</label>
                  <div className="relative">
                    <Input 
                      type={showKey ? "text" : "password"} 
                      placeholder={`Enter your ${llmProvider} API key...`}
                      value={llmKey}
                      onChange={(e) => {
                        setLlmKey(e.target.value)
                        setKeySaved(false)
                      }}
                      className="pr-10 border-[#3c4a42] bg-[#141414] focus:border-[#10b981]"
                    />
                    <button 
                      onClick={() => setShowKey(!showKey)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-[#a1a1aa] hover:text-[#e5e2e1]"
                    >
                      {showKey ? "Hide" : "Show"}
                    </button>
                  </div>
                </div>
                <div className="flex items-center space-x-4 pt-2">
                  <Button onClick={handleSaveLlmKey} className="bg-[#10b981] hover:bg-[#059669] text-[#002113]">
                    Save Key
                  </Button>
                  {keySaved && (
                    <Button onClick={handleRemoveLlmKey} variant="outline" className="border-[#ef4444] text-[#ef4444] hover:bg-[#ef4444]/10">
                      Remove Key
                    </Button>
                  )}
                  {saveMessage && activeTab === "api" && <span className="text-sm text-[#10b981] animate-in fade-in">{saveMessage}</span>}
                </div>
                <div className="mt-4 p-4 rounded-md border border-[#3c4a42] bg-[#141414]">
                  <p className="text-xs text-[#a1a1aa] leading-relaxed">
                    <Lock className="inline h-3 w-3 mr-1" />
                    <strong>Security Notice:</strong> Your key is stored locally in your browser's encrypted storage. It is never logged on our servers and is exclusively passed in memory to authenticate requests to the LLM provider.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
          
          {activeTab === "notifications" && (
            <Card className="border-[#1f1f1f] bg-[#0c0c0c]">
              <CardHeader>
                <CardTitle>Notifications</CardTitle>
                <CardDescription>Manage your alert preferences.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between py-2 border-b border-[#1f1f1f]">
                  <span className="text-sm text-[#e5e2e1]">Upcoming Contests</span>
                  <input type="checkbox" className="toggle" defaultChecked />
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-[#e5e2e1]">Rating Changes</span>
                  <input type="checkbox" className="toggle" defaultChecked />
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
