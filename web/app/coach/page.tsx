"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useModelInfo, useTeams, useSeasons } from "@/hooks/use-api";
import { useAppStore } from "@/hooks/use-app-store";
import api from "@/lib/api-client";
import { Dribbble, Send, MessageSquare, User, Bot, Trash2, Download } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function CoachPage() {
  const { currentSeason, currentLeague, myTeamId } = useAppStore();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [context, setContext] = useState(""); 
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: modelInfo } = useModelInfo();
  const { data: seasonsData } = useSeasons(currentLeague);
  const { data: teamsData } = useTeams(currentSeason, currentLeague);

  const teams = teamsData?.teams || [];
  const myTeam = teams.find((t) => t.id === myTeamId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const ctx = params.get("context");
      if (ctx) {
        setContext(ctx);
      }
    }
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await api.askCoach({
        question: userMessage,
        context: context,
        team_id: myTeamId || undefined,
        season: currentSeason,
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `${response.model}\n\n${response.response}` },
      ]);
    } catch (error) {
      console.error("Error asking coach:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error. Please try again." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setContext("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDownload = () => {
    if (messages.length === 0) return;

    const text = messages
      .map((msg) => `### ${msg.role === "user" ? "You" : "Coach"}\n${msg.content}`)
      .join("\n\n---\n\n");

    const blob = new Blob([text], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `coach-conversation-${new Date().toISOString().split("T")[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <MessageSquare className="w-8 h-8 text-primary" />
              <h1 className="text-3xl font-bold">Coach's Corner</h1>
            </div>
            <div className="flex items-center gap-2">
              {modelInfo && (
                <Badge variant="secondary">
                  <Bot className="w-4 h-4 mr-1" />
                  {modelInfo.model}
                </Badge>
              )}
              {messages.length > 0 && (
                <Button variant="outline" size="sm" onClick={handleDownload}>
                  <Download className="w-4 h-4 mr-1" />
                  Export
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 container mx-auto px-4 py-8 flex gap-6">
        {/* Sidebar - Context */}
        <aside className="w-72 flex-shrink-0">
          <Card className="sticky top-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Dribbble className="w-5 h-5" />
                Team Context
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Current Team */}
              <div>
                <label className="text-sm font-medium mb-2 block">Your Team</label>
                {myTeam ? (
                  <Badge variant="secondary" className="text-xs">
                    {myTeam.name}
                  </Badge>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Select your team from the dashboard
                  </p>
                )}
              </div>

              {/* Season */}
              <div>
                <label className="text-sm font-medium mb-2 block">Season</label>
                <select
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  value={currentSeason}
                  disabled
                >
                  {seasonsData?.seasons.map((season) => (
                    <option key={season} value={season}>
                      {season}
                    </option>
                  ))}
                </select>
              </div>

              {/* Context Input */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Additional Context
                </label>
                <textarea
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm min-h-[150px] resize-y"
                  placeholder="Add any additional context about the game, players, or situation..."
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                />
              </div>

              {/* Session Info */}
              <div className="pt-4 border-t border-border">
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Messages:</span>
                  <span className="font-medium">{messages.length}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </aside>

        {/* Chat Area */}
        <main className="flex-1 flex flex-col">
          <Card className="flex-1 flex flex-col">
            {/* Messages */}
            <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                  <MessageSquare className="w-16 h-16 text-primary/20" />
                  <div>
                    <h3 className="text-xl font-semibold mb-2">
                      Welcome to Coach's Corner
                    </h3>
                    <p className="text-muted-foreground max-w-md">
                      I'm your AI assistant coach. Ask me about tactics, plays, practice
                      drills, or analysis using your team's data.
                    </p>
                  </div>
                  <div className="space-y-2 text-left text-sm text-muted-foreground max-w-md">
                    <p>• "What offense should we run against zone defense?"</p>
                    <p>• "Help me scout {teams[0]?.name || "our opponent"}</p>
                    <p>• "What drills should we practice for better 3-point shooting?"</p>
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`flex items-start gap-3 max-w-[80%] ${
                          message.role === "user" ? "flex-row-reverse" : ""
                        }`}
                      >
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                            message.role === "user"
                              ? "bg-primary text-primary-foreground"
                              : "bg-secondary text-secondary-foreground"
                          }`}
                        >
                          {message.role === "user" ? (
                            <User className="w-4 h-4" />
                          ) : (
                            <Bot className="w-4 h-4" />
                          )}
                        </div>
                        <div
                          className={`rounded-lg px-4 py-3 ${
                            message.role === "user"
                              ? "bg-primary text-primary-foreground"
                              : "bg-secondary text-secondary-foreground"
                          }`}
                        >
                          {message.role === "assistant" && message.content.includes("\n\n") ? (
                            <div className="prose prose-invert max-w-none">
                              {message.content.split("\n\n").map((part, i) => {
                                if (part.includes("⚡") || part.includes("🧠") || part.includes("💻")) {
                                  return (
                                    <Badge key={i} variant="secondary" className="mb-2 block">
                                      {part}
                                    </Badge>
                                  );
                                }
                                return <p key={i}>{part}</p>;
                              })}
                            </div>
                          ) : (
                            <p className="whitespace-pre-wrap">{message.content}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center">
                          <Bot className="w-4 h-4" />
                        </div>
                        <div className="bg-secondary text-secondary-foreground rounded-lg px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-current rounded-full animate-bounce" />
                            <div className="w-2 h-2 bg-current rounded-full animate-bounce delay-100" />
                            <div className="w-2 h-2 bg-current rounded-full animate-bounce delay-200" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </CardContent>

            {/* Input */}
            <div className="p-4 border-t border-border">
              <div className="flex gap-2">
                <Input
                  placeholder="Ask the coach..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button
                  onClick={handleSend}
                  disabled={isLoading || !input.trim()}
                  size="sm"
                >
                  {isLoading ? (
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>
              {messages.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClear}
                  className="mt-2 w-full"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clear Conversation
                </Button>
              )}
            </div>
          </Card>
        </main>
      </div>
    </div>
  );
}
