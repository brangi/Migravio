"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import { Link } from "@/i18n/navigation";
import { useRouter } from "@/i18n/navigation";
import { useEffect, useState, useRef } from "react";
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
  const tNav = useTranslations("nav");
  const tFooter = useTranslations("footer");
  const { user, profile, loading, signOut, refreshProfile } = useAuth();
  const router = useRouter();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const [escalationKeywords, setEscalationKeywords] = useState<string[]>([]);
  const [showEscalation, setShowEscalation] = useState(false);

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
          title: data.title || "New conversation",
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
      title: "New conversation",
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
      alert(t("limitReached"));
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
          language: profile.language,
          visa_type: profile.visaType,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
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
              "Sorry, something went wrong. Please try again or contact an attorney if this is urgent.",
          };
          return updated;
        });
      }
    } finally {
      setIsStreaming(false);
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

  // Render message content with basic markdown support
  const renderMessageContent = (content: string) => {
    // Simple markdown parsing for bold, lists, and links
    let html = content
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="text-blue-600 underline" target="_blank" rel="noopener noreferrer">$1</a>')
      .replace(/\n/g, "<br/>");

    return <div dangerouslySetInnerHTML={{ __html: html }} />;
  };

  if (loading || !user || !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  const messagesRemaining = Math.max(0, 10 - profile.messageCount);
  const isFreeUser = profile.subscription.plan === "free";

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Top nav */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="text-gray-600 hover:text-gray-900 md:hidden"
              aria-label="Toggle sidebar"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <Link href="/dashboard" className="text-xl font-bold text-blue-700">
              Migravio
            </Link>
          </div>
          <h1 className="hidden text-sm font-medium text-gray-600 md:block">
            {t("title")}
          </h1>
          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              {tNav("dashboard")}
            </Link>
            <Link
              href="/chat"
              className="text-sm font-medium text-blue-600"
            >
              {tNav("chat")}
            </Link>
            <Link
              href="/attorneys"
              className="text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              {tNav("attorneys")}
            </Link>
          </nav>
          <button
            onClick={signOut}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            {tNav("signOut")}
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - Desktop */}
        <aside className="hidden w-64 border-r border-gray-200 bg-white md:block">
          <div className="flex h-full flex-col">
            <div className="border-b border-gray-200 p-4">
              <button
                onClick={createNewSession}
                className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                {t("newChat")}
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => switchSession(session.id)}
                  className={`mb-1 w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                    currentSessionId === session.id
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  <div className="truncate font-medium">{session.title}</div>
                  <div className="mt-0.5 truncate text-xs text-gray-500">
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
              className="absolute left-0 top-0 h-full w-64 bg-white"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex h-full flex-col">
                <div className="flex items-center justify-between border-b border-gray-200 p-4">
                  <span className="text-sm font-medium text-gray-900">
                    Conversations
                  </span>
                  <button
                    onClick={() => setShowSidebar(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <svg
                      className="h-5 w-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
                <div className="border-b border-gray-200 p-4">
                  <button
                    onClick={createNewSession}
                    className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    {t("newChat")}
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2">
                  {sessions.map((session) => (
                    <button
                      key={session.id}
                      onClick={() => switchSession(session.id)}
                      className={`mb-1 w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                        currentSessionId === session.id
                          ? "bg-blue-50 text-blue-700"
                          : "text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      <div className="truncate font-medium">{session.title}</div>
                      <div className="mt-0.5 truncate text-xs text-gray-500">
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
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-6 pb-32 md:pb-6">
            <div className="mx-auto max-w-3xl">
              {messages.length === 0 ? (
                <div className="flex h-full items-center justify-center">
                  <div className="text-center">
                    <div className="mb-4 text-4xl">💬</div>
                    <h2 className="text-lg font-semibold text-gray-900">
                      {t("title")}
                    </h2>
                    <p className="mt-2 text-sm text-gray-500">
                      {t("placeholder")}
                    </p>
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
                        className={`max-w-[85%] rounded-2xl px-4 py-2.5 md:max-w-[75%] ${
                          message.role === "user"
                            ? "bg-blue-600 text-white"
                            : "bg-white text-gray-900 shadow-sm"
                        }`}
                      >
                        <div className="text-sm leading-relaxed">
                          {message.role === "user" ? (
                            message.content
                          ) : (
                            renderMessageContent(message.content)
                          )}
                        </div>
                        {message.model && (
                          <div className="mt-1 text-xs text-gray-400">
                            {message.model.includes("sonnet") ? "Claude Sonnet" : "Claude Haiku"}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {isStreaming && messages[messages.length - 1]?.content === "" && (
                    <div className="mb-4 flex justify-start">
                      <div className="max-w-[75%] rounded-2xl bg-white px-4 py-2.5 shadow-sm">
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <div className="flex gap-1">
                            <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]"></div>
                            <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]"></div>
                            <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></div>
                          </div>
                          {t("thinking")}
                        </div>
                      </div>
                    </div>
                  )}

                  {showEscalation && (
                    <div className="mb-4">
                      <div className="rounded-lg border-2 border-amber-200 bg-amber-50 p-4">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0">
                            <svg
                              className="h-6 w-6 text-amber-600"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                              />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-amber-900">
                              {t("escalation.title")}
                            </h3>
                            <p className="mt-1 text-sm text-amber-800">
                              {t("escalation.description")}
                            </p>
                            <Link
                              href="/attorneys"
                              className="mt-3 inline-flex items-center rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
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

          {/* Input area - Fixed at bottom */}
          <div className="border-t border-gray-200 bg-white px-4 py-4 md:px-6">
            <div className="mx-auto max-w-3xl">
              {isFreeUser && (
                <div className="mb-2 text-center text-xs text-gray-500">
                  {messagesRemaining > 0 ? (
                    t("messagesRemaining", {
                      count: messagesRemaining,
                      total: 10,
                    })
                  ) : (
                    <span className="font-medium text-amber-600">
                      {t("limitReached")}{" "}
                      <Link href="/pricing" className="underline">
                        {t("upgrade")}
                      </Link>
                    </span>
                  )}
                </div>
              )}

              <form onSubmit={sendMessage} className="flex gap-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t("placeholder")}
                  disabled={isStreaming || (isFreeUser && messagesRemaining === 0)}
                  className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
                  rows={1}
                  style={{
                    minHeight: "48px",
                    maxHeight: "120px",
                  }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = "48px";
                    target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
                  }}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isStreaming || (isFreeUser && messagesRemaining === 0)}
                  className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors hover:bg-blue-700 disabled:bg-gray-300"
                  aria-label={t("send")}
                >
                  {isStreaming ? (
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  ) : (
                    <svg
                      className="h-5 w-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                      />
                    </svg>
                  )}
                </button>
              </form>

              <div className="mt-2 text-center text-xs text-gray-400">
                {t("disclaimer")}
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 border-t border-gray-200 bg-white md:hidden">
        <div className="flex justify-around py-2">
          <Link
            href="/dashboard"
            className="flex flex-col items-center p-2 text-xs font-medium text-gray-500"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
            {tNav("dashboard")}
          </Link>
          <Link
            href="/chat"
            className="flex flex-col items-center p-2 text-xs font-medium text-blue-600"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            {tNav("chat")}
          </Link>
          <Link
            href="/attorneys"
            className="flex flex-col items-center p-2 text-xs font-medium text-gray-500"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {tNav("attorneys")}
          </Link>
        </div>
      </nav>

      {/* Footer - Desktop only */}
      <footer className="hidden border-t border-gray-100 bg-gray-50 py-4 text-center text-xs text-gray-500 md:block">
        {tFooter("disclaimer")}
      </footer>
    </div>
  );
}
