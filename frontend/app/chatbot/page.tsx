"use client";

import { useEffect, useRef, useState } from "react";
import { MessageSquare, Send, Loader2 } from "lucide-react";
import Cookies from "js-cookie";
import { useAuthGuard } from "@/lib/useAuthGuard";
import { ChatMessage } from "@/types";

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_BASE_URL || "ws://localhost:8000/api/v1";

export default function ChatbotPage() {
  const { ready } = useAuthGuard();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [waitingReply, setWaitingReply] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ready) return;
    const token = Cookies.get("access_token");
    if (!token) return;

    const ws = new WebSocket(`${WS_BASE_URL}/chat/ws?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.error) {
        setWaitingReply(false);
        return;
      }
      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply, ts: new Date().toISOString() },
      ]);
      setWaitingReply(false);
    };

    return () => ws.close();
  }, [ready]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function sendMessage() {
    if (!input.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const userMessage: ChatMessage = { role: "user", content: input, ts: new Date().toISOString() };
    setMessages((prev) => [...prev, userMessage]);
    wsRef.current.send(JSON.stringify({ session_id: sessionId, message: input }));
    setInput("");
    setWaitingReply(true);
  }

  if (!ready) return null;

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-brand-700">
          <MessageSquare className="w-6 h-6" />
          <h1 className="text-2xl font-bold">Legal AI Chatbot</h1>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${connected ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
          {connected ? "Connected" : "Connecting..."}
        </span>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto card mb-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400 text-center py-10">
            Ask any question about the Bharatiya Nyaya Sanhita — e.g. "What is the punishment for theft in a dwelling house?"
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                m.role === "user" ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-800"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {waitingReply && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-2xl px-4 py-2.5 text-sm flex items-center gap-2 text-slate-500">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Thinking...
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          className="input-field"
          placeholder="Type your legal question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage} disabled={!connected} className="btn-primary flex items-center gap-1.5">
          <Send className="w-4 h-4" /> Send
        </button>
      </div>
      <p className="text-xs text-slate-400 mt-2">
        AI-generated preliminary information only — not a substitute for professional legal advice.
      </p>
    </div>
  );
}
