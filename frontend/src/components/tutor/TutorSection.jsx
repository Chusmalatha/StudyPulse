import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MessageSquare,
  Plus,
  Send,
  Loader2,
  FileText,
  AlertTriangle,
  Sparkles,
  Bot,
  User,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
} from 'lucide-react';
import tutorService from '../../services/api/tutorService';
import FormattedMarkdown from '../common/FormattedMarkdown';

const TutorSection = ({ projectId }) => {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [questionInput, setQuestionInput] = useState('');
  const [isLoadingConvs, setIsLoadingConvs] = useState(true);
  const [isLoadingMsgs, setIsLoadingMsgs] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  useEffect(() => {
    setActiveConversationId(null);
    setMessages([]);
    setError(null);
  }, [projectId]);

  // Load conversations list for project
  const loadConversations = useCallback(async () => {
    setIsLoadingConvs(true);
    try {
      const data = await tutorService.getConversations(projectId);
      setConversations(data);
      if (data.length > 0) {
        const exists = data.some((c) => c.id === activeConversationId);
        if (!activeConversationId || !exists) {
          setActiveConversationId(data[0].id);
        }
      } else {
        setActiveConversationId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setIsLoadingConvs(false);
    }
  }, [projectId, activeConversationId]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Load messages for active conversation
  const loadMessages = useCallback(async (convId) => {
    if (!convId) return;
    setIsLoadingMsgs(true);
    // Clear previous error state so stale banners don't persist
    setError(null);
    try {
      const data = await tutorService.getMessages(projectId, convId);
      setMessages(data);
    } catch (err) {
      // Gracefully handle missing/deleted conversation ID without showing red banner
      if (err.response?.status === 404) {
        setActiveConversationId(null);
        setMessages([]);
      } else {
        setError(err.response?.data?.detail || 'Failed to load messages.');
      }
    } finally {
      setIsLoadingMsgs(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (activeConversationId) {
      loadMessages(activeConversationId);
    }
  }, [activeConversationId, loadMessages]);

  // Create new conversation
  const handleCreateConversation = async () => {
    setError(null);
    try {
      const newConv = await tutorService.createConversation(projectId);
      setConversations((prev) => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setMessages([]);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create conversation.');
    }
  };

  // Send message to Tutor
  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!questionInput.trim() || isSending) return;
    setError(null);

    let targetConvId = activeConversationId;

    // Create conversation on the fly if none exists or if it's invalid string
    if (!targetConvId || targetConvId === 'undefined' || targetConvId === 'null') {
      try {
        const newConv = await tutorService.createConversation(projectId);
        setConversations((prev) => [newConv, ...prev]);
        setActiveConversationId(newConv.id);
        targetConvId = newConv.id;
      } catch (err) {
        alert('Failed to start conversation.');
        return;
      }
    }

    const currentText = questionInput.trim();
    setQuestionInput('');
    setIsSending(true);

    // Optimistically insert user message
    const tempUserMsg = {
      id: `temp-${Date.now()}`,
      conversation_id: targetConvId,
      project_id: projectId,
      user_id: 'me',
      role: 'user',
      content: currentText,
      citations: [],
      grounded: true,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const tutorResp = await tutorService.sendMessage(projectId, targetConvId, currentText);

      // Refresh conversations list to update title if changed
      loadConversations();

      const tempAstMsg = {
        id: tutorResp.message_id,
        conversation_id: targetConvId,
        project_id: projectId,
        user_id: 'tutor',
        role: 'assistant',
        content: tutorResp.answer,
        citations: tutorResp.citations || [],
        grounded: tutorResp.grounded,
        unsupported: tutorResp.unsupported,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, tempAstMsg]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get answer from AI Tutor.');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col h-[calc(100dvh-220px)] min-h-[500px] overflow-hidden">
      {/* Top: conversation list (mobile: horizontal scroll strip; desktop: left panel) */}
      <div className="flex flex-col md:flex-row flex-1 overflow-hidden">
      {/* Sidebar / Conversation Drawer */}
      <div className="w-full md:w-72 border-b md:border-b-0 md:border-r border-gray-200 bg-gray-50/50 flex flex-col max-h-36 md:max-h-full shrink-0">
        <div className="p-3 border-b border-gray-200 flex items-center justify-between bg-white">
          <div className="flex items-center gap-2 text-gray-900 font-semibold text-sm">
            <MessageSquare size={16} className="text-indigo-600" />
            <span className="text-sm">Discussions</span>
          </div>
          <button
            onClick={handleCreateConversation}
            className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1.5 rounded-lg transition-colors cursor-pointer"
          >
            <Plus size={14} />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          {isLoadingConvs ? (
            <div className="flex items-center justify-center py-10 text-gray-400 gap-2 text-xs">
              <Loader2 size={16} className="animate-spin text-indigo-600" />
              <span>Loading history...</span>
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-10 px-4 text-gray-400">
              <Sparkles size={24} className="mx-auto mb-2 opacity-50 text-indigo-500" />
              <p className="text-xs font-medium text-gray-600">No conversations yet</p>
              <p className="text-[11px] text-gray-400 mt-1">Start a discussion with your Project Tutor.</p>
            </div>
          ) : (
            conversations.map((conv, idx) => (
              <button
                key={conv.id || `conv-${idx}`}
                onClick={() => setActiveConversationId(conv.id)}
                className={`w-full text-left p-3 rounded-xl transition-all cursor-pointer border ${
                  activeConversationId === conv.id
                    ? 'bg-white border-indigo-200 shadow-xs ring-1 ring-indigo-500/20'
                    : 'border-transparent hover:bg-gray-100/70 text-gray-700'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-gray-900 truncate">{conv.title}</p>
                  <ChevronRight
                    size={14}
                    className={`shrink-0 transition-transform ${
                      activeConversationId === conv.id ? 'text-indigo-600 transform translate-x-0.5' : 'text-gray-300'
                    }`}
                  />
                </div>
                <p className="text-[10px] text-gray-400 mt-1 flex items-center gap-1">
                  <Clock size={10} />
                  {new Date(conv.last_message_at || conv.created_at).toLocaleDateString()}
                </p>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main Tutor Chat Interface */}
      <div className="flex-1 flex flex-col bg-white relative overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-white z-10 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center font-bold">
              <Bot size={20} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                Project AI Tutor
                <span className="bg-indigo-50 text-indigo-700 text-[10px] font-bold px-2 py-0.5 rounded-full border border-indigo-100">
                  Grounded RAG
                </span>
              </h3>
              <p className="text-[11px] text-gray-500">
                Answers strictly from uploaded Project learning material with page citations.
              </p>
            </div>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-5 bg-gradient-to-b from-white to-gray-50/30">
          {isLoadingMsgs ? (
            <div className="flex items-center justify-center py-20 text-gray-400 gap-2 text-xs">
              <Loader2 size={20} className="animate-spin text-indigo-600" />
              <span>Fetching conversation messages...</span>
            </div>
          ) : messages.length === 0 ? (
            <div className="max-w-md mx-auto my-12 text-center space-y-4">
              <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto shadow-xs">
                <Sparkles size={24} />
              </div>
              <div>
                <h4 className="text-sm font-bold text-gray-900">Ask your Project Tutor anything</h4>
                <p className="text-xs text-gray-500 mt-1">
                  Try asking simple explanations, comparisons, or real-world examples supported by your study material.
                </p>
              </div>

              {/* Sample Prompts */}
              <div className="grid grid-cols-1 gap-2 pt-2 text-left">
                {[
                  'Explain the main concepts in simple terms.',
                  'Give me a practical example based on the PDF.',
                  'Compare the key methods discussed in the material.',
                ].map((promptText, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuestionInput(promptText);
                    }}
                    className="text-xs bg-white hover:bg-indigo-50/50 text-gray-700 hover:text-indigo-700 p-3 rounded-xl border border-gray-200 hover:border-indigo-200 transition-all text-left shadow-2xs cursor-pointer flex items-center justify-between"
                  >
                    <span>"{promptText}"</span>
                    <ChevronRight size={14} className="text-gray-400" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={msg.id || `msg-${idx}`}
                className={`flex gap-3 max-w-3xl ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold ${
                    msg.role === 'user'
                      ? 'bg-violet-600 text-white shadow-xs'
                      : 'bg-indigo-600 text-white shadow-xs'
                  }`}
                >
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>

                {/* Message Bubble */}
                <div className={`space-y-2 max-w-[85%] ${msg.role === 'user' ? 'items-end' : ''}`}>
                  <div
                    className={`p-4 rounded-2xl text-xs leading-relaxed shadow-xs ${
                      msg.role === 'user'
                        ? 'bg-violet-600 text-white rounded-tr-xs'
                        : 'bg-white border border-gray-200 text-gray-800 rounded-tl-xs'
                    }`}
                  >
                    <FormattedMarkdown content={msg.content} isUser={msg.role === 'user'} />
                  </div>

                  {/* Unsupported Notice Banner */}
                  {msg.role === 'assistant' && (msg.unsupported || !msg.grounded) && (
                    <div className="bg-amber-50 border border-amber-200/80 rounded-xl p-3 flex items-start gap-2 text-amber-900 text-[11px]">
                      <AlertTriangle size={15} className="text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <p className="font-semibold text-amber-950">Unsupported Question Refusal</p>
                        <p className="text-amber-800 mt-0.5">
                          The available Project materials do not contain sufficient evidence to answer this confidently.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Citation Sources Badges */}
                  {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                    <div className="bg-indigo-50/60 border border-indigo-100 rounded-xl p-3 space-y-2">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-indigo-900 uppercase tracking-wider">
                        <BookOpen size={13} className="text-indigo-600" />
                        <span>Sources & Citations</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {msg.citations.map((cite, idx) => (
                          <div
                            key={idx}
                            className="bg-white border border-indigo-200 text-indigo-950 px-2.5 py-1.5 rounded-lg text-[11px] flex items-center gap-1.5 shadow-2xs font-medium"
                          >
                            <FileText size={12} className="text-indigo-600" />
                            <span className="font-semibold max-w-[140px] truncate">{cite.filename}</span>
                            <span className="text-indigo-400">•</span>
                            <span className="bg-indigo-100 text-indigo-800 font-bold px-1.5 py-0.2 rounded text-[10px]">
                              Page {cite.page_number}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Thinking Loading Indicator */}
          {isSending && (
            <div className="flex gap-3 max-w-3xl">
              <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 text-xs font-bold shadow-xs">
                <Bot size={16} />
              </div>
              <div className="p-4 rounded-2xl rounded-tl-xs bg-white border border-gray-200 shadow-xs flex items-center gap-2 text-xs text-gray-500 font-medium">
                <Loader2 size={16} className="animate-spin text-indigo-600" />
                <span>Tutor is retrieving project knowledge & thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-gray-200 bg-white">
          {error && (
            <div className="mb-3 p-2.5 bg-red-50 text-red-700 rounded-lg text-xs flex items-center justify-between border border-red-100">
              <span>{error}</span>
              <button onClick={() => setError(null)} className="font-bold hover:underline cursor-pointer">
                Dismiss
              </button>
            </div>
          )}

          <form onSubmit={handleSendMessage} className="flex items-center gap-2">
            <input
              type="text"
              value={questionInput}
              onChange={(e) => setQuestionInput(e.target.value)}
              placeholder="Ask a question about your Project materials..."
              disabled={isSending}
              className="flex-1 text-xs border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-50"
            />
            <button
              type="submit"
              disabled={!questionInput.trim() || isSending}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3 rounded-xl text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 shadow-xs cursor-pointer"
            >
              {isSending ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <>
                  <span>Send</span>
                  <Send size={14} />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
      </div>
    </div>
  );
};

export default TutorSection;
