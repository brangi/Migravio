"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link } from "@/i18n/navigation";
import { useRouter } from "@/i18n/navigation";
import { useEffect, useState, useRef, Fragment } from "react";
import {
  collection,
  query,
  orderBy,
  onSnapshot,
  doc,
  setDoc,
  updateDoc,
  serverTimestamp,
  getDoc,
  Timestamp,
} from "firebase/firestore";
import { db } from "@/lib/firebase";
import { AppHeader } from "@/components/app-header";
import { MobileNav } from "@/components/mobile-nav";
import { Logo } from "@/components/logo";
import { Send, Plus, X, AlertTriangle, Menu, MessageCircle, Clock, FileText, Sparkles, ArrowRight } from "@/components/icons";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  model?: string;
  escalated?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
}

export default function ChatPage() {
  const t = useTranslations("chat");
  const { user, profile, loading, refreshProfile } = useAuth();
  const router = useRouter();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isWarmingUp, setIsWarmingUp] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const [escalationKeywords, setEscalationKeywords] = useState<string[]>([]);
  const [showEscalation, setShowEscalation] = useState(false);
  const warmupTimerRef = useRef<NodeJS.Timeout | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Redirect if not authenticated or onboarding incomplete
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
    if (!loading && user && profile && !profile.onboardingComplete) {
      router.push("/onboarding");
    }
  }, [loading, user, profile, router]);

  // Load chat sessions from Firestore
  useEffect(() => {
    if (!user) return;

    const sessionsRef = collection(db, "users", user.uid, "chatSessions");
    const q = query(sessionsRef, orderBy("updatedAt", "desc"));

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const loadedSessions: ChatSession[] = [];
      snapshot.forEach((doc) => {
        const data = doc.data();
        loadedSessions.push({
          id: doc.id,
          title: data.title || t("newChat"),
          createdAt: data.createdAt?.toDate() || new Date(),
          updatedAt: data.updatedAt?.toDate() || new Date(),
          messages: data.messages || [],
        });
      });
      setSessions(loadedSessions);

      // Auto-select first session or create new if none exist
      if (loadedSessions.length > 0 && !currentSessionId) {
        setCurrentSessionId(loadedSessions[0].id);
        setMessages(loadedSessions[0].messages);
      }
    });

    return () => unsubscribe();
  }, [user, currentSessionId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Create new chat session
  const createNewSession = async () => {
    if (!user) return;

    const newSessionId = `session_${Date.now()}`;
    const sessionRef = doc(db, "users", user.uid, "chatSessions", newSessionId);

    await setDoc(sessionRef, {
      title: t("newChat"),
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
      messages: [],
    });

    setCurrentSessionId(newSessionId);
    setMessages([]);
    setShowEscalation(false);
    setShowSidebar(false);
  };

  // Switch to existing session
  const switchSession = (sessionId: string) => {
    const session = sessions.find((s) => s.id === sessionId);
    if (session) {
      setCurrentSessionId(sessionId);
      setMessages(session.messages);
      setShowEscalation(
        session.messages.some((msg) => msg.escalated === true)
      );
      setShowSidebar(false);
    }
  };

  // Send message with SSE streaming
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !user || !profile || isStreaming) return;

    // Check message limit for free users
    if (
      profile.subscription.plan === "free" &&
      profile.messageCount >= 10
    ) {
      return;
    }

    const userMessage: Message = {
      role: "user",
      content: input.trim(),
      timestamp: Date.now(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setIsStreaming(true);
    setIsWarmingUp(false);
    warmupTimerRef.current = setTimeout(() => setIsWarmingUp(true), 8000);

    // Create empty assistant message for streaming
    const assistantMessage: Message = {
      role: "assistant",
      content: "",
      timestamp: Date.now(),
    };
    setMessages([...updatedMessages, assistantMessage]);

    try {
      const idToken = await user.getIdToken();
      const apiUrl =
        process.env.NEXT_PUBLIC_AI_SERVICE_URL || "http://localhost:8000";

      abortControllerRef.current = new AbortController();

      const response = await fetch(`${apiUrl}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: currentSessionId,
          language: isFreeUser ? "en" : profile.language,
          visa_type: profile.visaType,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        if (response.status === 429) {
          await refreshProfile();
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let streamedContent = "";
      let detectedModel = "";
      let isEscalated = false;

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const jsonStr = line.slice(6).trim();
              if (jsonStr === "[DONE]") continue;

              try {
                const event = JSON.parse(jsonStr);

                if (event.type === "model") {
                  detectedModel = event.data;
                } else if (event.type === "content") {
                  if (warmupTimerRef.current) { clearTimeout(warmupTimerRef.current); warmupTimerRef.current = null; }
                  setIsWarmingUp(false);
                  streamedContent += event.data;
                  setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                      ...updated[updated.length - 1],
                      content: streamedContent,
                      model: detectedModel,
                    };
                    return updated;
                  });
                } else if (event.type === "escalation") {
                  isEscalated = true;
                  setEscalationKeywords(event.keywords || []);
                  setShowEscalation(true);
                } else if (event.type === "done") {
                  break;
                }
              } catch (parseError) {
                console.error("Error parsing SSE event:", parseError);
              }
            }
          }
        }
      }

      // Final assistant message
      const finalAssistantMessage: Message = {
        role: "assistant",
        content: streamedContent,
        timestamp: Date.now(),
        model: detectedModel,
        escalated: isEscalated,
      };

      const finalMessages = [...updatedMessages, finalAssistantMessage];
      setMessages(finalMessages);

      // Save to Firestore
      if (currentSessionId) {
        const sessionRef = doc(
          db,
          "users",
          user.uid,
          "chatSessions",
          currentSessionId
        );

        // Generate title from first message if needed
        const sessionSnap = await getDoc(sessionRef);
        const currentTitle = sessionSnap.data()?.title || "New conversation";
        const newTitle =
          currentTitle === "New conversation" && userMessage.content.length > 0
            ? userMessage.content.slice(0, 50) +
              (userMessage.content.length > 50 ? "..." : "")
            : currentTitle;

        await updateDoc(sessionRef, {
          title: newTitle,
          updatedAt: serverTimestamp(),
          messages: finalMessages.map((msg) => ({
            ...msg,
            timestamp: Timestamp.fromMillis(msg.timestamp),
          })),
        });
      } else {
        // Create new session if none exists
        const newSessionId = `session_${Date.now()}`;
        const sessionRef = doc(
          db,
          "users",
          user.uid,
          "chatSessions",
          newSessionId
        );
        const newTitle =
          userMessage.content.slice(0, 50) +
          (userMessage.content.length > 50 ? "..." : "");

        await setDoc(sessionRef, {
          title: newTitle,
          createdAt: serverTimestamp(),
          updatedAt: serverTimestamp(),
          messages: finalMessages.map((msg) => ({
            ...msg,
            timestamp: Timestamp.fromMillis(msg.timestamp),
          })),
        });

        setCurrentSessionId(newSessionId);
      }

      // Refresh profile to update message count
      await refreshProfile();
    } catch (error: any) {
      if (error.name === "AbortError") {
        console.log("Request aborted");
      } else {
        console.error("Error sending message:", error);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content:
              t("errorMessage"),
          };
          return updated;
        });
      }
    } finally {
      setIsStreaming(false);
      setIsWarmingUp(false);
      if (warmupTimerRef.current) clearTimeout(warmupTimerRef.current);
      abortControllerRef.current = null;
    }
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e);
    }
  };

  // Render message content as plain text (strip any markdown that slips through)
  const renderMessageContent = (content: string) => {
    const clean = content
      // Strip markdown headers
      .replace(/^#{1,6}\s+/gm, "")
      // Convert bold to plain text
      .replace(/\*\*(.*?)\*\*/g, "$1")
      // Convert italic to plain text
      .replace(/\*(.*?)\*/g, "$1")
      // Convert markdown links to just the text
      .replace(/\[(.*?)\]\(.*?\)/g, "$1")
      // Convert markdown bullet dashes to plain dashes
      .replace(/^[-*]\s+/gm, "- ")
      // Collapse triple+ newlines to double
      .replace(/\n{3,}/g, "\n\n");

    const lines = clean.split("\n");
    return (
      <div>
        {lines.map((line, i) => (
          <Fragment key={i}>
            {line}
            {i < lines.length - 1 && <br />}
          </Fragment>
        ))}
      </div>
    );
  };

  if (loading || !user || !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  const messagesRemaining = Math.max(0, 10 - profile.messageCount);
  const isFreeUser = profile.subscription.plan === "free";

  return (
    <div className="flex h-screen flex-col bg-surface">
      {/* Header */}
      <AppHeader activePage="chat" />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - Desktop */}
        <aside className="relative hidden w-64 border-r border-border-strong bg-surface-alt shadow-[2px_0_8px_-2px_oklch(0.20_0.02_275_/_0.06)] md:block">
          <div className="flex h-full flex-col">
            <div className="border-b border-border-strong p-4">
              <button
                onClick={createNewSession}
                className="w-full rounded-lg bg-accent-500 px-4 py-2 text-sm font-medium text-white hover:bg-accent-600 transition-colors inline-flex items-center justify-center gap-2"
              >
                <Plus className="h-4 w-4" />
                {t("newChat")}
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => switchSession(session.id)}
                  className={`mb-1 w-full rounded-lg px-3 py-2 text-left text-sm transition-all relative ${
                    currentSessionId === session.id
                      ? "bg-surface text-text-primary border-l-2 border-primary-600"
                      : "text-text-secondary hover:bg-surface/50"
                  }`}
                >
                  <div className="truncate font-medium">{session.title}</div>
                  <div className="mt-0.5 truncate text-xs text-text-tertiary">
                    {session.updatedAt.toLocaleDateString()}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Sidebar - Mobile */}
        {showSidebar && (
          <div className="fixed inset-0 z-50 bg-black/50 md:hidden" onClick={() => setShowSidebar(false)}>
            <aside
              className="absolute left-0 top-0 h-full w-64 bg-surface-alt shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex h-full flex-col">
                <div className="flex items-center justify-between border-b border-border-strong p-4">
                  <span className="text-sm font-medium text-text-primary">
                    {t("conversationsLabel")}
                  </span>
                  <button
                    onClick={() => setShowSidebar(false)}
                    className="text-text-secondary hover:text-text-primary"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
                <div className="border-b border-border-strong p-4">
                  <button
                    onClick={createNewSession}
                    className="w-full rounded-lg bg-accent-500 px-4 py-2 text-sm font-medium text-white hover:bg-accent-600 inline-flex items-center justify-center gap-2"
                  >
                    <Plus className="h-4 w-4" />
                    {t("newChat")}
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2">
                  {sessions.map((session) => (
                    <button
                      key={session.id}
                      onClick={() => switchSession(session.id)}
                      className={`mb-1 w-full rounded-lg px-3 py-2 text-left text-sm transition-all relative ${
                        currentSessionId === session.id
                          ? "bg-surface text-text-primary border-l-2 border-primary-600"
                          : "text-text-secondary hover:bg-surface/50"
                      }`}
                    >
                      <div className="truncate font-medium">{session.title}</div>
                      <div className="mt-0.5 truncate text-xs text-text-tertiary">
                        {session.updatedAt.toLocaleDateString()}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </aside>
          </div>
        )}

        {/* Main chat area */}
        <main className="flex flex-1 flex-col">
          {/* Mobile menu button */}
          <div className="flex items-center gap-3 border-b border-border-strong bg-surface px-4 py-3 md:hidden">
            <button
              onClick={() => setShowSidebar(true)}
              className="text-text-secondary hover:text-text-primary"
              aria-label="Toggle sidebar"
            >
              <Menu className="h-5 w-5" />
            </button>
            <h1 className="text-sm font-medium text-text-secondary">{t("title")}</h1>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-6 pb-36 md:pb-8">
            <div className="mx-auto max-w-3xl">
              {messages.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center px-4">
                  <div className="text-center">
                    <div className="mb-4 inline-flex">
                      <Logo size="lg" variant="icon" />
                    </div>
                    <h2 className="font-display text-2xl font-semibold text-text-primary">
                      {t("title")}
                    </h2>
                    <p className="mt-2 text-base text-text-secondary">
                      {t("subtitle")}
                    </p>
                  </div>

                  {/* Starter Prompts */}
                  <div className="mt-8 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
                    {([
                      { icon: Clock, labelKey: "starterPrompts.visaRenewal" as const },
                      { icon: FileText, labelKey: "starterPrompts.documents" as const },
                      { icon: Sparkles, labelKey: "starterPrompts.statusChange" as const },
                      { icon: ArrowRight, labelKey: "starterPrompts.greenCard" as const },
                    ]).map((prompt) => (
                      <button
                        key={prompt.labelKey}
                        type="button"
                        onClick={() => setInput(t(prompt.labelKey))}
                        className="group flex items-start gap-3 rounded-xl border border-border bg-surface p-4 text-left text-base text-text-secondary shadow-sm transition-all hover:border-primary-300 hover:shadow-md hover:text-text-primary"
                      >
                        <prompt.icon className="mt-0.5 h-4 w-4 flex-shrink-0 text-primary-400 transition-colors group-hover:text-primary-600" />
                        <span>{t(prompt.labelKey)}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`mb-4 flex ${
                        message.role === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[85%] px-4 py-2.5 md:max-w-[75%] ${
                          message.role === "user"
                            ? "bg-primary-600 text-white rounded-2xl rounded-br-md"
                            : "bg-surface-alt border border-border text-text-primary rounded-2xl rounded-bl-md"
                        }`}
                      >
                        <div className="text-base leading-relaxed">
                          {message.role === "user" ? (
                            message.content
                          ) : (
                            renderMessageContent(message.content)
                          )}
                        </div>
                      </div>
                    </div>
                  ))}

                  {isStreaming && messages[messages.length - 1]?.content === "" && (
                    <div className="mb-4 flex justify-start">
                      <div className="max-w-[75%] rounded-2xl rounded-bl-md bg-surface-alt border border-border px-4 py-2.5">
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-2 text-sm text-text-secondary">
                            <div className="flex gap-1">
                              <div className="h-2 w-2 animate-bounce rounded-full bg-text-tertiary [animation-delay:-0.3s]"></div>
                              <div className="h-2 w-2 animate-bounce rounded-full bg-text-tertiary [animation-delay:-0.15s]"></div>
                              <div className="h-2 w-2 animate-bounce rounded-full bg-text-tertiary"></div>
                            </div>
                            {t("thinking")}
                          </div>
                          {isWarmingUp && (
                            <p className="text-xs text-text-tertiary">
                              {t("warmingUp")}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {showEscalation && (
                    <div className="mb-4">
                      <div className="rounded-lg border-l-4 border-warning bg-warning/5 p-4">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0">
                            <AlertTriangle className="h-6 w-6 text-warning" />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-text-primary">
                              {t("escalation.title")}
                            </h3>
                            <p className="mt-1 text-base text-text-secondary">
                              {t("escalation.description")}
                            </p>
                            <Link
                              href="/attorneys"
                              className="mt-3 inline-flex items-center rounded-lg bg-warning px-4 py-2 text-sm font-medium text-white hover:bg-warning/90 transition-colors"
                            >
                              {t("escalation.cta")}
                            </Link>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </>
              )}
            </div>
          </div>

          {/* Input area */}
          <div className="bg-gradient-to-t from-surface via-surface to-transparent px-4 pb-4 pt-3 md:px-6">
            <div className="mx-auto max-w-3xl">
              {/* Messages remaining badge */}
              {isFreeUser && (
                <div className="mb-3 flex justify-center">
                  {messagesRemaining > 0 ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-alt px-3 py-1 text-xs text-text-secondary">
                      <MessageCircle className="h-3 w-3" />
                      {t("messagesRemaining", {
                        count: messagesRemaining,
                        total: 10,
                      })}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-warning/20 bg-warning/10 px-3 py-1 text-xs font-medium text-warning">
                      <AlertTriangle className="h-3 w-3" />
                      {t("limitReached")}{" "}
                      <Link href="/pricing" className="underline transition-colors hover:text-warning/80">
                        {t("upgrade")}
                      </Link>
                    </span>
                  )}
                </div>
              )}

              {/* Input card */}
              <form onSubmit={sendMessage}>
                <div className="flex items-end gap-2 overflow-hidden rounded-2xl border-2 border-primary-200 bg-surface px-3 py-2 shadow-lg transition-all focus-within:border-primary-500 focus-within:shadow-xl">
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={t("placeholder")}
                    disabled={isStreaming || (isFreeUser && messagesRemaining === 0)}
                    className="block flex-1 resize-none border-0 bg-transparent px-1 py-1 text-base text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-0 disabled:text-text-tertiary"
                    rows={1}
                    style={{
                      minHeight: "36px",
                      maxHeight: "120px",
                    }}
                    onInput={(e) => {
                      const target = e.target as HTMLTextAreaElement;
                      target.style.height = "36px";
                      target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
                    }}
                  />
                  <button
                    type="submit"
                    disabled={!input.trim() || isStreaming || (isFreeUser && messagesRemaining === 0)}
                    className="mb-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-600 text-white transition-all hover:bg-primary-700 disabled:bg-surface-alt disabled:text-text-tertiary"
                    aria-label={t("send")}
                  >
                    {isStreaming ? (
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </form>

              {/* Disclaimer — separate from input */}
              <p className="mt-2 text-center text-xs text-text-tertiary">
                {t("disclaimer")}
              </p>
            </div>
          </div>
        </main>
      </div>

      {/* Mobile Nav */}
      <MobileNav activePage="chat" />
    </div>
  );
}
