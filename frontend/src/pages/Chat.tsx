import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Send, Loader2, X, Mic, MessageSquarePlus, Menu, MessageCircle, PanelLeftClose, PanelLeft, Pencil, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage as ChatMessageType, ChatModel } from "@/lib/chat-api";
import { sendChatMessage } from "@/lib/chat-api";
import * as chatSessions from "@/lib/chat-sessions";
import { getMe } from "@/lib/credits-api";
import type { ChatSession } from "@/lib/chat-sessions";
import { useLocation } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import { AppNavbar } from "@/components/AppNavbar";
import { toast } from "@/hooks/use-toast";

type SpeechRecognitionInstance = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: (event: {
    resultIndex: number;
    results: { length: number; isFinal: boolean; [0]: { transcript: string } }[];
  }) => void;
  onend: () => void;
  onerror: (event: { error: string }) => void;
};

const SpeechRecognitionAPI =
  typeof window !== "undefined"
    ? ((window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance }).SpeechRecognition ||
        (window as unknown as { webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).webkitSpeechRecognition)
    : undefined;

const INITIAL_ASSISTANT_MESSAGE =
  "Hello! I'm **Stock Sense AI**. You can ask me to:\n\n- **Analyze AAPL** – full report with trend and levels\n- **Scan market** – find opportunities\n- **Seasonality for NVDA** – seasonal report\n- **Risk 10000 on GOOGL** – position sizing";

function rewriteChartUrls(content: string): string {
  return content
    .replace(/https?:\/\/rakeshent\.info\/chart_img/g, "/chart_img")
    .replace(/https?:\/\/rakeshent\.info\/chart_v2/g, "/chart_v2")
    .replace(/http:\/\/localhost:5000\/chart_img/g, "/chart_img")
    .replace(/http:\/\/localhost:5000\/chart_v2/g, "/chart_v2");
}

const markdownComponents = {
  table: ({ children, ...props }: React.HTMLAttributes<HTMLTableElement>) => (
    <div className="my-3 w-full overflow-x-auto">
      <table className="min-w-full border-collapse border border-border" {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({ children, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) => (
    <th className="border border-border bg-muted/50 px-2 py-1.5 text-left font-medium" {...props}>
      {children}
    </th>
  ),
  td: ({ children, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) => (
    <td className="border border-border px-2 py-1.5" {...props}>
      {children}
    </td>
  ),
  img: ({ src, alt, ...props }: React.ImgHTMLAttributes<HTMLImageElement>) => (
    <span className="my-2 block overflow-hidden rounded-lg border border-border bg-muted/30">
      <img
        src={src}
        alt={alt ?? "Chart"}
        className="max-w-full w-full h-auto object-contain"
        loading="lazy"
        referrerPolicy="no-referrer"
        {...props}
      />
    </span>
  ),
  a: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary underline hover:no-underline"
      {...props}
    >
      {children}
    </a>
  ),
};

function truncateTitle(text: string, max = 28): string {
  const t = text.trim();
  if (t.length <= max) return t;
  return t.slice(0, max) + "…";
}

export default function Chat() {
  const { user, loading: authLoading, idToken, getIdToken } = useAuth();
  const [, setLocation] = useLocation();
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageType[]>([{ role: "assistant", content: INITIAL_ASSISTANT_MESSAGE }]);
  const [loadingChatList, setLoadingChatList] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState<ChatModel>("stock-gita-model");
  const [isListening, setIsListening] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [deleteConfirmChatId, setDeleteConfirmChatId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  const loadChatList = useCallback(async () => {
    if (!idToken) return;
    setLoadingChatList(true);
    try {
      const list = await chatSessions.listChats(idToken);
      setChats(list);
    } catch (e) {
      console.warn("Failed to load chat list:", e);
      toast({ title: "Could not load chats", description: e instanceof Error ? e.message : "Unknown error", variant: "destructive" });
    } finally {
      setLoadingChatList(false);
    }
  }, [idToken]);

  useEffect(() => {
    if (!authLoading && !user) setLocation("/auth");
  }, [authLoading, user, setLocation]);

  useEffect(() => {
    if (user && idToken) loadChatList();
  }, [user, idToken, loadChatList]);

  const loadChat = useCallback(
    async (chatId: string) => {
      if (!idToken) return;
      setLoadingChat(true);
      setSidebarOpen(false);
      try {
        const chat = await chatSessions.getChat(idToken, chatId);
        setCurrentChatId(chat.id);
        setMessages(
          chat.messages.length
            ? chat.messages
            : [{ role: "assistant" as const, content: INITIAL_ASSISTANT_MESSAGE }]
        );
      } catch (e) {
        toast({ title: "Could not load chat", description: e instanceof Error ? e.message : "Unknown error", variant: "destructive" });
      } finally {
        setLoadingChat(false);
      }
    },
    [idToken]
  );

  const startNewChat = useCallback(() => {
    setCurrentChatId(null);
    setMessages([{ role: "assistant", content: INITIAL_ASSISTANT_MESSAGE }]);
    setSidebarOpen(false);
  }, []);

  const openDeleteConfirm = useCallback((chatId: string) => {
    setDeleteConfirmChatId(chatId);
  }, []);

  const closeDeleteConfirm = useCallback(() => {
    setDeleteConfirmChatId(null);
  }, []);

  const confirmDeleteChat = useCallback(async () => {
    const chatId = deleteConfirmChatId;
    if (!idToken || !chatId) return;
    setDeleteConfirmChatId(null);
    try {
      await chatSessions.deleteChat(idToken, chatId);
      setChats((prev) => prev.filter((c) => c.id !== chatId));
      if (currentChatId === chatId) startNewChat();
      setEditingChatId(null);
      toast({ title: "Chat deleted" });
    } catch (e) {
      toast({ title: "Could not delete chat", description: e instanceof Error ? e.message : "Unknown error", variant: "destructive" });
    }
  }, [idToken, deleteConfirmChatId, currentChatId, startNewChat]);

  const handleStartEdit = useCallback((chat: ChatSession) => {
    setEditingChatId(chat.id);
    setEditingTitle(chat.title);
  }, []);

  const handleSaveEdit = useCallback(
    async (chatId: string) => {
      const title = editingTitle.trim() || "New chat";
      if (!idToken) return;
      setEditingChatId(null);
      try {
        await chatSessions.updateChatTitle(idToken, chatId, title);
        setChats((prev) => prev.map((c) => (c.id === chatId ? { ...c, title } : c)));
      } catch (e) {
        toast({ title: "Could not rename chat", description: e instanceof Error ? e.message : "Unknown error", variant: "destructive" });
      }
    },
    [idToken, editingTitle]
  );

  useEffect(() => {
    const scrollToBottom = () => scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    scrollToBottom();
    if (loading) {
      const t = requestAnimationFrame(() => requestAnimationFrame(scrollToBottom));
      return () => cancelAnimationFrame(t);
    }
  }, [messages, loading]);

  const toggleVoiceInput = useCallback(() => {
    if (!SpeechRecognitionAPI) {
      toast({ title: "Voice input not supported", description: "Use Chrome or Edge for voice-to-text.", variant: "destructive" });
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.onresult = (event: Parameters<SpeechRecognitionInstance["onresult"]>[0]) => {
      let finalText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) finalText += event.results[i][0].transcript;
      }
      if (finalText) setInput((prev) => (prev + finalText).trim());
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = (event: Parameters<SpeechRecognitionInstance["onerror"]>[0]) => {
      if (event.error !== "aborted") {
        toast({ title: "Voice input error", description: event.error === "not-allowed" ? "Microphone access denied." : String(event.error), variant: "destructive" });
      }
      setIsListening(false);
    };
    recognitionRef.current = recognition;
    try {
      recognition.start();
      setIsListening(true);
    } catch {
      toast({ title: "Voice input failed", description: "Could not start microphone.", variant: "destructive" });
      setIsListening(false);
    }
  }, [isListening]);

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
    };
  }, []);

  const MIN_CREDITS_TO_CHAT = 100;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading || !user) return;

    const token = await getIdToken();
    if (!token) {
      toast({ title: "Authentication failed", description: "Please sign in again.", variant: "destructive" });
      return;
    }

    try {
      const me = await getMe(token);
      if (me.credits < MIN_CREDITS_TO_CHAT) {
        toast({
          title: "Insufficient credits",
          description: `You need at least ${MIN_CREDITS_TO_CHAT} credits to chat. You have ${me.credits.toLocaleString()}. Add credits in Profile.`,
          variant: "destructive",
        });
        return;
      }
    } catch {
      toast({ title: "Could not check credits", variant: "destructive" });
      return;
    }

    const userMessage: ChatMessageType = { role: "user", content: text };
    setInput("");
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    let chatId = currentChatId;
    try {
      if (!chatId) {
        const title = truncateTitle(text, 40);
        const created = await chatSessions.createChat(token, title);
        chatId = created.id;
        setCurrentChatId(chatId);
        setChats((prev) => [{ id: created.id, title: created.title }, ...prev]);
      }
      await chatSessions.addMessage(token, chatId, "user", text);

      const nextMessages: ChatMessageType[] = [...messages, userMessage];
      const result = await sendChatMessage(nextMessages, model, token);
      const content = result.content;
      setMessages((prev) => [...prev, { role: "assistant", content }]);
      await chatSessions.addMessage(token, chatId, "assistant", content);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Something went wrong.";
      const isInsufficientCredits = errorMessage.toLowerCase().includes("insufficient credits");
      const isAuthError = errorMessage.toLowerCase().includes("authentication");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: isInsufficientCredits
            ? `**Insufficient credits**\n\n${errorMessage}\n\nAdd credits in your [Profile](/profile) to continue.`
            : isAuthError
              ? `**Authentication required**\n\n${errorMessage}\n\nPlease [sign out](/auth) and sign in again to refresh your session.`
              : `**Error**\n\n${errorMessage}\n\nPlease check that the backend is running and try again.`,
        },
      ]);
      toast({
        title: isInsufficientCredits ? "Insufficient credits" : isAuthError ? "Authentication required" : "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  const renderSidebarContent = (expanded: boolean) => (
    <div className="flex flex-col h-full">
      <div className={`flex gap-1.5 mb-3 ${!expanded ? "flex-col items-center" : "items-center"}`}>
        {expanded ? (
          <button
            type="button"
            onClick={startNewChat}
            className="flex-1 min-w-0 flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium text-foreground hover:bg-muted/60 active:bg-muted/80 transition-colors"
          >
            <MessageSquarePlus className="w-4 h-4 shrink-0 text-muted-foreground" />
            New Chat
          </button>
        ) : (
          <button
            type="button"
            onClick={startNewChat}
            className="shrink-0 p-2 rounded-xl text-muted-foreground hover:bg-muted/60 hover:text-foreground transition-colors"
            title="New Chat"
          >
            <MessageSquarePlus className="w-4 h-4" />
          </button>
        )}
        <button
          type="button"
          onClick={() => setSidebarCollapsed((c) => !c)}
          className="shrink-0 p-2 rounded-xl text-muted-foreground hover:bg-muted/60 hover:text-foreground transition-colors lg:flex hidden items-center justify-center"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? <PanelLeft className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
        </button>
      </div>
      {expanded && (
        <>
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 px-1">
            Recent chats
          </div>
          <div className="flex-1 overflow-y-auto space-y-0.5 min-h-0">
            {loadingChatList ? (
              <p className="text-sm text-muted-foreground py-4">Loading…</p>
            ) : chats.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4">No chats yet. Start a new chat above.</p>
            ) : (
              chats.map((chat) => (
                <div
                  key={chat.id}
                  className={`group group/item group flex items-center gap-1 w-full rounded-lg border transition-colors ${
                    currentChatId === chat.id
                      ? "bg-primary/15 border-primary/30"
                      : "border-transparent hover:bg-muted/60"
                  }`}
                >
                  {editingChatId === chat.id ? (
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onBlur={() => handleSaveEdit(chat.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleSaveEdit(chat.id);
                        if (e.key === "Escape") setEditingChatId(null);
                      }}
                      className="flex-1 min-w-0 px-2 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/30"
                      autoFocus
                    />
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => loadChat(chat.id)}
                        className="flex-1 min-w-0 text-left px-3 py-2.5 text-sm truncate transition-colors text-foreground"
                        title={chat.title}
                      >
                        <span className="flex items-center gap-2">
                          <MessageCircle className="w-4 h-4 shrink-0 text-muted-foreground" />
                          {truncateTitle(chat.title)}
                        </span>
                      </button>
                      <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity shrink-0 pr-1">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartEdit(chat);
                          }}
                          className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/80"
                          aria-label="Rename chat"
                          title="Rename"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            openDeleteConfirm(chat.id);
                          }}
                          className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                          aria-label="Delete chat"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );

  if (authLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <AppNavbar />
        <main className="flex-1 flex items-center justify-center p-6 md:p-12 lg:p-16 max-w-6xl mx-auto w-full">
          <p className="text-muted-foreground">Loading…</p>
        </main>
      </div>
    );
  }
  if (!user) {
    return null;
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <AppNavbar fixed />

      <AlertDialog open={deleteConfirmChatId !== null} onOpenChange={(open: boolean) => !open && closeDeleteConfirm()}>
        <AlertDialogContent className="sm:max-w-md border-border bg-card">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-foreground">Delete this chat?</AlertDialogTitle>
            <AlertDialogDescription>
              This cannot be undone. All messages in this chat will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2 sm:gap-0">
            <AlertDialogCancel onClick={closeDeleteConfirm} className="border-border">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteChat}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="flex flex-1 min-h-0 overflow-hidden pt-14">
        {/* Sidebar – fixed on the side, only main content scrolls */}
        <aside
          className={`hidden lg:flex flex-col shrink-0 h-full border-r border-border bg-card/50 transition-[width] duration-200 overflow-hidden ${
            sidebarCollapsed ? "w-16 p-2" : "w-64 p-4"
          }`}
        >
          {renderSidebarContent(!sidebarCollapsed)}
        </aside>

        <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden fixed top-16 left-4 z-40 border border-border bg-card/80"
              aria-label="Open chat list"
            >
              <Menu className="w-5 h-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[min(20rem,85vw)] p-4 flex flex-col">
            <div className="flex-1 flex flex-col min-h-0 mt-2">
              {renderSidebarContent(true)}
            </div>
          </SheetContent>
        </Sheet>

        {/* Main chat area – scrollable, overscroll contained so navbar stays fixed */}
        <main className="flex-1 flex flex-col min-w-0 min-h-0 overflow-y-auto overflow-x-hidden overscroll-contain p-3 sm:p-6 lg:p-8 pl-4 sm:pl-6 lg:pl-8 pt-6 sm:pt-8">
          <div className="max-w-4xl mx-auto w-full flex flex-col min-w-0">
          {loadingChat ? (
            <div className="flex-1 flex items-center justify-center py-12">
              <p className="text-muted-foreground">Loading chat…</p>
            </div>
          ) : (
            <div className="space-y-4 sm:space-y-6 pt-12 pb-36 sm:pb-32">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={
                    msg.role === "user"
                      ? "flex justify-end"
                      : "flex justify-start"
                  }
                >
                  <Card
                    className={
                      msg.role === "user"
                        ? "max-w-[92%] sm:max-w-[75%] bg-primary/15 border-primary/30 text-foreground"
                        : "w-full max-w-full bg-card/80 border-border overflow-hidden"
                    }
                  >
                    <div className="flex gap-2 p-3 sm:p-4">
                      <div
                        className={
                          msg.role === "user"
                            ? "break-words"
                            : "prose prose-invert prose-sm max-w-none break-words [&_table]:text-xs [&_th]:px-2 [&_td]:px-2 [&_ul]:my-2 [&_ol]:my-2 [&_img]:max-w-full"
                        }
                      >
                        {msg.role === "user" ? (
                          <p className="m-0 whitespace-pre-wrap">{msg.content}</p>
                        ) : (
                          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                            {rewriteChartUrls(msg.content)}
                          </ReactMarkdown>
                        )}
                      </div>
                    </div>
                  </Card>
                </div>
              ))}
              {loading && (
                <div className="w-full">
                  <Card className="w-full bg-card/80 border-border">
                    <div className="flex gap-2 p-3 sm:p-4">
                      <Loader2 className="w-5 h-5 text-primary animate-spin shrink-0" />
                      <span className="text-muted-foreground text-sm">Thinking…</span>
                    </div>
                  </Card>
                </div>
              )}
              <div ref={scrollRef} className="h-0 w-full shrink-0" aria-hidden />
            </div>
          )}
          </div>
        </main>
      </div>

      {/* Fixed input bar – full width on mobile, solid background like ChatGPT */}
      <div
        className={`fixed inset-x-0 bottom-0 z-30 border-t border-border bg-background/95 backdrop-blur-md pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:pt-4 sm:pb-4 transition-[margin-left] duration-200 ${
          sidebarCollapsed ? "lg:ml-16" : "lg:ml-64"
        }`}
      >
        <div className="max-w-4xl mx-auto px-3 sm:px-6 lg:px-8">
          <form
            onSubmit={handleSubmit}
            className="rounded-2xl sm:rounded-[1.25rem] border border-border bg-card shadow-sm flex items-stretch gap-2 p-2 sm:p-3 min-h-[48px] sm:min-h-[52px]"
          >
            <button
                type="button"
                onClick={() => setInput("")}
                className="hidden sm:flex shrink-0 p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors self-center items-center justify-center"
                aria-label="Clear"
              >
                <X className="w-4 h-4" />
              </button>
            <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Analyze AAPL, Scan market..."
                className="min-h-[40px] sm:min-h-[44px] max-h-[200px] sm:max-h-[280px] resize-none flex-1 min-w-0 bg-muted/40 border-0 rounded-xl shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-muted-foreground py-2.5 px-2 sm:px-3 text-sm sm:text-base"
                rows={1}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
            <div className="flex items-center gap-2 shrink-0 border-l border-border pl-2 sm:pl-2.5">
              <div className="hidden sm:block">
                <Select value={model} onValueChange={(v) => setModel(v as ChatModel)}>
                  <SelectTrigger className="w-[120px] lg:w-[140px] h-9 border-border bg-background rounded-lg">
                    <SelectValue placeholder="Model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="stock-gita-model">Pro (default)</SelectItem>
                    <SelectItem value="stock-gita-master">Master</SelectItem>
                    <SelectItem value="stock-gita-seasonality">Seasonality</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <button
                type="button"
                onClick={toggleVoiceInput}
                className={`rounded-full h-9 w-9 sm:h-10 sm:w-10 flex items-center justify-center border transition-colors shrink-0 ${
                  isListening ? "border-destructive bg-destructive/20 text-destructive" : "border-border text-foreground hover:bg-muted/50"
                }`}
                aria-label={isListening ? "Stop listening" : "Voice input"}
                title={isListening ? "Stop listening" : "Voice to text"}
              >
                <Mic className="w-5 h-5" />
              </button>
              <Button
                type="submit"
                disabled={loading || !input.trim()}
                className="rounded-full h-9 w-9 sm:h-10 sm:w-10 p-0 shrink-0"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
