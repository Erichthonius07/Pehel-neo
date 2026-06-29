"use client";

import { useState, useEffect, useRef } from "react";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { chatApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  text: string;
}

export default function ChatPageClient({ id }: { id: string }) {
  const { citizenToken } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !citizenToken || !id || id === "demo") return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    try {
      const res = await chatApi.ask(id, question, citizenToken);
      const answer = (res as any).answer || "No response from assistant.";
      setMessages((prev) => [...prev, { role: "assistant", text: answer }]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Error: Could not reach the assistant." },
      ]);
    }
    setLoading(false);
  };

  const displayId = id && id !== "demo" ? id.slice(0, 8) : "DEMO";

  return (
    <LayoutShell>
      <Link
        href={`/issues/${id}`}
        className="text-xs uppercase text-text-secondary hover:text-text-primary mb-4 inline-flex items-center gap-2"
      >
        <ArrowLeft size={14} /> BACK TO ISSUE
      </Link>

      <h1 className="text-4xl font-extrabold text-text-primary mb-2">ISSUE CHAT</h1>
      <div className="chapter-break mb-6" />
      <p className="mono-text text-text-secondary mb-8">ISSUE #{displayId}</p>

      <div className="border border-border-light bg-white h-[600px] flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <p className="text-sm text-text-secondary">
                {id === "demo" ? "This is a demo chat page." : "Ask a question about this issue."}
              </p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[70%] p-4 text-sm ${
                  msg.role === "user"
                    ? "bg-text-primary text-white"
                    : "bg-surface-secondary text-text-primary border border-border-light"
                }`}
              >
                <p className="text-[10px] uppercase tracking-wider mb-1 opacity-70">
                  {msg.role === "user" ? "You" : "Assistant"}
                </p>
                <p className="whitespace-pre-line">{msg.text}</p>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-surface-secondary border border-border-light p-4">
                <p className="mono-text text-xs text-text-secondary">Thinking...</p>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="border-t border-border-light p-4 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type your question..."
            className="flex-1 h-12 px-4 border-2 border-border-medium bg-surface-elevated text-sm focus:border-text-primary outline-none"
          />
          <Button onClick={handleSend} disabled={loading || !input.trim() || id === "demo"} size="icon">
            <Send size={16} />
          </Button>
        </div>
      </div>
    </LayoutShell>
  );
}