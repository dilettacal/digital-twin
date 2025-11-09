"use client";

import { useState, useRef, useEffect } from "react";
import type { KeyboardEvent } from "react";
import { Send, Bot, User } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function Twin() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const timestamp = Date.now();
    const userMessage: Message = {
      id: timestamp.toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };
    const assistantMessageId = `${timestamp}-assistant`;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const updateAssistantContent = (content: string) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId ? { ...msg, content } : msg,
          ),
        );
      };

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({
            message: input,
            session_id: sessionId || undefined,
          }),
        },
      );

      if (!response.ok) {
        // Try to parse error as JSON first (FastAPI returns JSON errors)
        let errorDetail = "";
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorData.message || "";
        } catch {
          errorDetail = await response.text();
        }

        console.error(`HTTP ${response.status}: ${errorDetail}`);

        // Handle different error types with user-friendly messages
        let errorMessage = "";

        if (response.status === 429) {
          // Rate limit error - show the server's message directly
          errorMessage = `⏱️ ${errorDetail}`;
        } else if (response.status === 400) {
          // Validation error - show the server's message
          errorMessage = `❌ ${errorDetail}`;
        } else if (response.status === 500) {
          errorMessage =
            "⚠️ Sorry, something went wrong on my end. Please try again in a moment.";
        } else {
          errorMessage = `⚠️ Error: ${errorDetail}`;
        }

        throw new Error(errorMessage);
      }

      const contentType = response.headers.get("content-type") || "";

      if (!contentType.includes("text/event-stream")) {
        const data = await response.json();

        if (data.session_id) {
          setSessionId((prev) => prev || data.session_id);
        }

        updateAssistantContent(data.response);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("⚠️ Streaming is not supported in this browser.");
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let accumulated = "";
      let streamError: string | null = null;
      let doneReceived = false;

      const processEvent = (rawEvent: string) => {
        if (!rawEvent.trim()) return;

        const lines = rawEvent.split("\n");
        let eventName = "message";
        let dataPayload = "";

        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventName = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            dataPayload += line.slice(5).trim();
          }
        }

        if (!dataPayload) return;

        let parsed;
        try {
          parsed = JSON.parse(dataPayload);
        } catch (error) {
          console.error("Failed to parse SSE data", error);
          return;
        }

        switch (eventName) {
          case "session": {
            if (parsed.session_id) {
              setSessionId((prev) => prev || parsed.session_id);
            }
            break;
          }
          case "token": {
            if (typeof parsed.delta === "string" && parsed.delta.length > 0) {
              accumulated += parsed.delta;
              updateAssistantContent(accumulated);
            }
            break;
          }
          case "done": {
            if (typeof parsed.response === "string") {
              accumulated = parsed.response;
              updateAssistantContent(parsed.response);
            }
            doneReceived = true;
            break;
          }
          case "error": {
            const detail =
              typeof parsed.detail === "string"
                ? parsed.detail
                : "⚠️ Streaming error occurred.";
            streamError = detail;
            updateAssistantContent(detail);
            doneReceived = true;
            break;
          }
          default:
            break;
        }
      };

      while (!doneReceived) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        let delimiterIndex = buffer.indexOf("\n\n");
        while (delimiterIndex !== -1) {
          const rawEvent = buffer.slice(0, delimiterIndex);
          buffer = buffer.slice(delimiterIndex + 2);
          processEvent(rawEvent);

          if (doneReceived) {
            break;
          }

          delimiterIndex = buffer.indexOf("\n\n");
        }
      }

      if (!doneReceived && accumulated.length > 0) {
        updateAssistantContent(accumulated);
      }

      if (streamError) {
        throw new Error(streamError);
      }
    } catch (error) {
      console.error("Error:", error);

      let errorMessage = "⚠️ Sorry, I encountered an error. Please try again.";
      if (error instanceof Error) {
        console.error("Error details:", error.message);
        errorMessage = error.message;
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: errorMessage }
            : msg,
        ),
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden border border-gray-200 dark:border-gray-700 transition-colors duration-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-600 via-emerald-600 to-cyan-600 text-white p-5 rounded-t-xl">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm p-0.5">
              <div className="w-full h-full rounded-full bg-white dark:bg-gray-800 flex items-center justify-center shadow-inner">
                <Bot className="w-7 h-7 text-teal-600 dark:text-emerald-400" />
              </div>
            </div>
            <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-emerald-400 rounded-full border-2 border-white"></div>
          </div>
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">Luna</h2>
            <p className="text-sm text-white/90 mt-0.5">
              Diletta&apos;s Professional Digital Twin
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-gradient-to-b from-gray-50 to-white dark:from-gray-800 dark:to-gray-900 transition-colors duration-200">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 dark:text-gray-400 mt-16">
            <div className="relative inline-block mb-6">
              <div className="w-24 h-24 rounded-full bg-white dark:bg-gray-800 flex items-center justify-center mx-auto shadow-xl ring-4 ring-teal-400 dark:ring-emerald-500">
                <Bot className="w-12 h-12 text-teal-600 dark:text-emerald-400" />
              </div>
            </div>
            <p className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
              Hello! I&apos;m Luna
            </p>
            <p className="text-base text-gray-600 dark:text-gray-300 mb-4">
              Diletta&apos;s Professional Digital Twin
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
              Ask me about Diletta&apos;s work, experience, skills, and
              professional background.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 items-end ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {message.role === "assistant" && (
              <div className="flex-shrink-0 mb-1">
                <div className="w-10 h-10 rounded-full bg-white dark:bg-gray-800 flex items-center justify-center shadow-md ring-2 ring-teal-500 dark:ring-emerald-500">
                  <Bot className="w-5 h-5 text-teal-600 dark:text-emerald-400" />
                </div>
              </div>
            )}

            <div
              className={`max-w-[75%] rounded-2xl px-4 py-3 shadow-sm ${
                message.role === "user"
                  ? "bg-gradient-to-br from-teal-600 to-emerald-600 dark:from-teal-500 dark:to-emerald-600 text-white rounded-tr-sm"
                  : "bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-800 dark:text-gray-100 rounded-tl-sm shadow-sm"
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">
                {message.content}
              </p>
              <p
                className={`text-xs mt-2 ${
                  message.role === "user"
                    ? "text-white/70"
                    : "text-gray-400 dark:text-gray-400"
                }`}
              >
                {message.timestamp.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>

            {message.role === "user" && (
              <div className="flex-shrink-0 mb-1">
                <div className="w-10 h-10 rounded-full bg-white dark:bg-gray-800 flex items-center justify-center shadow-md ring-2 ring-teal-500 dark:ring-emerald-500">
                  <User className="w-5 h-5 text-teal-600 dark:text-emerald-400" />
                </div>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 justify-start items-end">
            <div className="flex-shrink-0 mb-1">
              <div className="w-10 h-10 rounded-full bg-white dark:bg-gray-800 flex items-center justify-center shadow-md ring-2 ring-teal-500 dark:ring-emerald-500">
                <Bot className="w-5 h-5 text-teal-600 dark:text-emerald-400" />
              </div>
            </div>
            <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
              <div className="flex space-x-1.5">
                <div
                  className="w-2 h-2 bg-teal-500 rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                />
                <div
                  className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"
                  style={{ animationDelay: "150ms" }}
                />
                <div
                  className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800 transition-colors duration-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your message..."
            maxLength={2000}
            className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 dark:focus:ring-emerald-400 focus:border-transparent text-gray-800 dark:text-gray-100 bg-white dark:bg-gray-700 placeholder-gray-400 dark:placeholder-gray-500 transition-all"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="px-5 py-3 bg-gradient-to-r from-teal-600 to-emerald-600 text-white rounded-xl hover:from-teal-700 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 shadow-md hover:shadow-lg"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        {input.length > 1800 && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-right">
            {input.length}/2000 characters
          </p>
        )}
      </div>
    </div>
  );
}
