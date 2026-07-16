import { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { addMessage, setLoading } from '../store/chatSlice';
import { populateFromAI, setStatus, setIsStatusPending } from '../store/formSlice';
import { sendMessage } from '../api';
import { Loader2 } from 'lucide-react';

export default function AgentChat() {
  const dispatch = useDispatch();
  const chatHistory = useSelector((s) => s.chat.messages);
  const isLoading = useSelector((s) => s.chat.isLoading);
  const isStatusPending = useSelector((s) => s.form.isStatusPending);
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatHistory, isLoading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;
    dispatch(addMessage({ role: 'user', content: text, toolsCalled: [] }));
    setInput('');
    dispatch(setLoading(true));
    dispatch(setIsStatusPending(true));
    try {
      const res = await sendMessage(text);
      dispatch(addMessage({
        role: 'ai',
        content: res.reply || 'Processing complete.',
        toolsCalled: res.tools_called || [],
        extractedData: res.extracted_data || null,
      }));
      if (res.extracted_data && Object.keys(res.extracted_data).length > 0) dispatch(populateFromAI(res.extracted_data));
      if (res.status) dispatch(setStatus(res.status));
    } catch (error) {
      console.error('Chat send error:', error);
      dispatch(addMessage({ role: 'ai', content: 'Sorry, something went wrong. Please try again.', toolsCalled: [] }));
    } finally {
      dispatch(setLoading(false));
      dispatch(setIsStatusPending(false));
    };
  };

  useEffect(() => {
    if (!isStatusPending || chatHistory.length === 0) return;
    const timer = setTimeout(() => {
      dispatch(setIsStatusPending(false));
      dispatch(setLoading(false));
      dispatch(addMessage({ role: 'ai', content: 'Request timed out. Please try again.', toolsCalled: [] }));
    }, 20000);
    return () => clearTimeout(timer);
  }, [isStatusPending, chatHistory, dispatch]);

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } };

  const isSuccessMessage = (msg) => {
    if (msg.role !== 'ai') return false;
    const c = (msg.content || '').toLowerCase();
    return c.includes('successfully') || c.includes('saved to database') || c.includes('\u2705');
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
        <pre className="bg-[#111827] text-emerald-400 p-3 rounded-lg text-[11px] font-mono overflow-x-auto mt-2 border border-gray-800">{formatted}</pre>
      );
    }
    const parts = msg.content.split(/(\*\*.*?\*\*)/g);
    return (
      <div className="whitespace-pre-wrap leading-relaxed text-sm text-gray-800">
        {parts.map((part, i) => {
          if (part.startsWith('**') && part.endsWith('**')) return <strong key={i} className="font-bold text-gray-900">{part.slice(2, -2)}</strong>;
          return part;
        })}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full min-h-0 bg-white">
      <div className="h-[56px] px-4 border-b border-gray-200 flex items-center justify-between bg-white shrink-0">
        <div className="flex items-center gap-3">
          {/* Logo/Avatar */}
          <div className="w-8 h-8 bg-[#2563eb] rounded-full flex items-center justify-center text-white shrink-0 shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z" />
              <path d="M17 22H7v-2a4 4 0 0 1 4-4h2a4 4 0 0 1 4 4v2z" />
              <path d="M9 16v-2h6v2" />
            </svg>
          </div>

          {/* Text Stack */}
          <div className="flex flex-col leading-tight">
            <span className="text-[14px] font-semibold text-gray-900">AI Assistant</span>
            <span className="text-[11px] text-gray-500 font-medium">Log Interaction details here via chat</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 bg-white scrollbar">
        {chatHistory.length === 0 && (
          <div className="flex justify-start my-2">
            <div className="max-w-[90%] bg-[#e0f2fe] border-[#bae6fd] rounded-xl px-4 py-3 text-sm text-gray-800 shadow-sm relative">
              <p>Hello! Describe your HCP interaction here, and I'll help you log it properly.</p>
            </div>
          </div>
        )}

        {chatHistory.map((msg, i) => {
          const isUser = msg.role === 'user';
          const isSuccess = !isUser && isSuccessMessage(msg);

          if (isUser) {
            return (
              <div key={i} className="flex justify-end mb-2">
                <div className="ml-auto bg-[#2563eb] text-white rounded-xl px-4 py-2.5 max-w-[80%] text-sm shadow-sm mb-2 leading-relaxed">
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            );
          }

          if (isSuccess) {
            return (
              <div key={i} className="flex justify-start w-full">
                <div className="w-full bg-[#f0fdf4] border border-[#bbf7d0] text-gray-800 px-4 py-3 rounded-xl text-sm shadow-sm leading-relaxed font-medium">
                  <div className="flex items-start gap-2.5">
                    <span className="text-emerald-600 text-sm mt-0.5 shrink-0">{'\u2705'}</span>
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
              </div>
            );
          }

          return (
            <div key={i} className="flex justify-start mb-2">
              <div className="mr-auto bg-white border border-gray-200 rounded-xl px-4 py-2.5 max-w-[80%] text-sm text-gray-800 shadow-sm mb-2 leading-relaxed">
                {renderMessageContent(msg)}
                {msg.extractedData && Object.keys(msg.extractedData).length > 0 && (
                  <pre className="bg-[#111827] text-emerald-400 p-3 rounded-lg text-[11px] font-mono overflow-x-auto mt-2 border border-gray-800">{JSON.stringify(msg.extractedData, null, 2)}</pre>
                )}
                {msg.toolsCalled?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5 pt-2 border-t border-gray-200">
                    {msg.toolsCalled.map((t, j) => (
                      <span key={j} className="inline-flex items-center gap-1 bg-gray-100 text-gray-700 text-[10px] px-2 py-[2px] rounded-full font-mono border border-gray-200 font-semibold">{t}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {(isStatusPending || isLoading) && (
          <div className="flex justify-start w-full">
            <div className="bg-[#ecfeff] border border-[#cffafe] text-gray-800 text-sm px-4 py-3 rounded-xl shadow-sm">
              <div className="flex items-center gap-1.5">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#2563eb]" />
                <span className="font-semibold">{isStatusPending ? 'Typing...' : 'Thinking...'}</span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 border-t border-gray-200 bg-white shrink-0 flex items-center gap-2 shadow-[0_-2px_10px_rgba(0,0,0,0.02)]">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Describe Interaction..."
          disabled={isLoading}
          className="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#2563eb] focus:border-[#2563eb] placeholder:text-gray-400"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="bg-[#2563eb] hover:bg-[#1d4ed8] text-white rounded-lg px-6 py-2.5 text-sm font-medium shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <span>Log</span>
          )}
        </button>
      </div>
    </div>
  );
}
