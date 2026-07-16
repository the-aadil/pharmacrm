import { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { addMessage, setLoading } from '../store/chatSlice';
import { populateFromAI, setStatus } from '../store/formSlice';
import { sendMessage } from '../api';
import { Loader2 } from 'lucide-react';

/* Robot icon — matches the reference emoji-style robot */
function RobotIcon({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <rect x="6" y="10" width="20" height="16" rx="4" fill="#8b5cf6" />
      <rect x="14" y="4" width="4" height="6" rx="2" fill="#a78bfa" />
      <circle cx="16" cy="4" r="2.5" fill="#c4b5fd" />
      <circle cx="12" cy="17" r="2.5" fill="white" />
      <circle cx="20" cy="17" r="2.5" fill="white" />
      <circle cx="12" cy="17" r="1.2" fill="#1e1b4b" />
      <circle cx="20" cy="17" r="1.2" fill="#1e1b4b" />
      <path d="M13 22 C14.5 23.5, 17.5 23.5, 19 22" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
      <rect x="2" y="14" width="4" height="6" rx="2" fill="#a78bfa" />
      <rect x="26" y="14" width="4" height="6" rx="2" fill="#a78bfa" />
    </svg>
  );
}

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, isLoading } = useSelector((s) => s.chat);
  const [input, setInput] = useState('');
  const bottomRef   = useRef(null);
  const textareaRef = useRef(null);
  const threadId    = useRef(Date.now().toString());

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, isLoading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;
    dispatch(addMessage({ role: 'user', content: text, toolsCalled: [] }));
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    dispatch(setLoading(true));
    try {
      const res = await sendMessage(text, threadId.current);
      dispatch(addMessage({ role: 'ai', content: res.reply || 'Processing complete.', toolsCalled: res.tools_called || [] }));
      if (res.extracted_data && Object.keys(res.extracted_data).length > 0) dispatch(populateFromAI(res.extracted_data));
      if (res.status) dispatch(setStatus(res.status));
    } catch {
      dispatch(addMessage({ role: 'ai', content: 'Sorry, something went wrong. Please try again.', toolsCalled: [] }));
    } finally {
      dispatch(setLoading(false));
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const isSuccessMessage = (msg) => {
    if (msg.role !== 'ai') return false;
    const c = (msg.content || '').toLowerCase();
    return c.includes('successfully') || c.includes('saved to database') || c.includes('✅');
  };

  const isJsonData = (content) => {
    if (!content || typeof content !== 'string') return false;
    const trimmed = content.trim();
    return trimmed.startsWith('{') && trimmed.includes('"hcp_name"');
  };

  const renderMessageContent = (msg) => {
    if (isJsonData(msg.content)) {
      let formatted = msg.content;
      try { formatted = JSON.stringify(JSON.parse(msg.content), null, 2); } catch {}
      return (
        <pre className="bg-[#111827] text-emerald-400 p-3 rounded-lg text-[11px] font-mono overflow-x-auto mt-2 border border-gray-800">
          {formatted}
        </pre>
      );
    }
    const parts = msg.content.split(/(\*\*.*?\*\*)/g);
    return (
      <p className="whitespace-pre-wrap leading-relaxed text-[13px]">
        {parts.map((part, i) => {
          if (part.startsWith('**') && part.endsWith('**'))
            return <strong key={i} className="font-bold text-[#111827]">{part.slice(2, -2)}</strong>;
          return part;
        })}
      </p>
    );
  };

  const hasInput = input.trim().length > 0;

  return (
    /* flex column: header pinned top, messages scroll middle, input pinned bottom */
    <div className="flex flex-col h-full bg-white">

      {/* ── Header ── */}
      <header className="flex items-center gap-4 py-3 bg-white shrink-0">
        <RobotIcon size={24} />
        <div>
          <h2 className="text-lg font-bold text-gray-900 leading-tight">AI Assistant</h2>
          <p className="text-[10px] uppercase font-bold tracking-tight text-gray-600 mt-1">Log Interaction details here via chat</p>
        </div>
      </header>

      {/* Divider */}
      <div className="border-t border-gray-200 mb-3 w-full" />

      {/* ── Messages: scrollable middle section ── */}
      <div
        className="flex-1 min-h-0 overflow-y-auto space-y-3 bg-white py-2"
        style={{ scrollbarWidth: 'thin', scrollbarColor: '#cbd5e1 transparent' }}
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-10">
            <p className="text-[13px] font-medium text-slate-400">No messages yet</p>
            <p className="text-[12px] text-slate-300 mt-1">Start by describing your HCP interaction</p>
          </div>
        )}

        {messages.map((msg, i) => {
          const isUser    = msg.role === 'user';
          const isSuccess = !isUser && isSuccessMessage(msg);

          /* User message */
          if (isUser) {
            return (
              <div key={i} className="flex justify-end w-full px-2">
                <div className="bg-blue-600 text-white rounded-2xl px-4 py-2 max-w-[80%] text-sm leading-relaxed">
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            );
          }

          /* Success message */
          if (isSuccess) {
            return (
              <div key={i} className="w-full bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-gray-800 leading-relaxed font-medium">
                <div className="flex items-start gap-2">
                  <span className="text-emerald-600 text-sm mt-0.5 shrink-0">✅</span>
                  <div className="flex-1 min-w-0">
                    {renderMessageContent(msg)}
                    {msg.toolsCalled?.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5 pt-2 border-t border-[#d1fae5]">
                        {msg.toolsCalled.map((t, j) => (
                          <span key={j} className="inline-flex items-center gap-1 bg-white text-[#059669] text-[10px] px-2 py-[2px] rounded-full font-mono border border-[#d1fae5] font-semibold">{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          }

          /* Regular AI message */
          return (
            <div key={i} className="w-full bg-teal-50/80 border border-teal-100 rounded-lg px-4 py-3 text-sm text-gray-800 leading-relaxed font-medium">
              {renderMessageContent(msg)}
              {msg.extractedData && Object.keys(msg.extractedData).length > 0 && (
                <pre className="bg-[#111827] text-emerald-400 p-3 rounded-lg text-[11px] font-mono overflow-x-auto mt-2 border border-gray-800">
                  {JSON.stringify(msg.extractedData, null, 2)}
                </pre>
              )}
              {msg.toolsCalled?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5 pt-2 border-t border-[#b2ebf2]">
                  {msg.toolsCalled.map((t, j) => (
                    <span key={j} className="inline-flex items-center gap-1 bg-white text-[#0891b2] text-[10px] px-2 py-[2px] rounded-full font-mono border border-[#b2ebf2] font-semibold">{t}</span>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="bg-teal-50/80 border border-teal-100 rounded-lg px-4 py-3 text-sm text-gray-800 w-full">
            <div className="flex items-center gap-1.5">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#2563eb]" />
              <span className="font-semibold">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Input row ── */}
      <div className="border-t border-gray-200 bg-white pt-3 pb-3 flex gap-4 items-end shrink-0">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            if (textareaRef.current) {
              textareaRef.current.style.height = 'auto';
              textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 100) + 'px';
            }
          }}
          onKeyDown={handleKeyDown}
          placeholder="Describe Interaction..."
          rows={1}
          className="flex-1 min-h-[40px] max-h-[100px] bg-white disabled:bg-gray-50 border border-gray-200 focus:border-[#2563eb] focus:ring-2 focus:ring-[#2563eb]/20 rounded-md p-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none resize-none transition-all duration-150"
          disabled={isLoading}
        />
        {/* Blue "A Log" button */}
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          className={`h-[40px] w-[52px] rounded-md flex flex-col items-center justify-center transition-all shrink-0 select-none
            ${hasInput
              ? 'bg-[#2563eb] text-white hover:bg-[#1d4ed8] shadow-sm cursor-pointer'
              : 'bg-gray-50 text-gray-400 border border-gray-200 cursor-not-allowed'
            }`}
        >
          <span className="text-[13px] font-bold leading-none mb-[2px]">A</span>
          <span className="text-[9px] font-bold uppercase tracking-wider leading-none">Log</span>
        </button>
      </div>
    </div>
  );
}
