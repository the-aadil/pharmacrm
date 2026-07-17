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
  const threadId = useSelector((s) => s.chat.threadId);
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatHistory, isLoading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;
    dispatch(addMessage({ role: 'user', content: text, toolsCalled: [] }));
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    dispatch(setLoading(true));
    dispatch(setIsStatusPending(true));
    try {
      const res = await sendMessage(text, threadId);
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
      textareaRef.current?.focus();
    };
  };

  useEffect(() => {
    if (!isStatusPending || chatHistory.length === 0) return;
    const timer = setTimeout(() => {
      dispatch(setIsStatusPending(false));
      dispatch(setLoading(false));
      dispatch(addMessage({ role: 'ai', content: 'Request timed out. Please try again.', toolsCalled: [] }));
    }, 35000);
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
        <pre style={{
          background: '#111827', color: '#6ee7b7', padding: '12px',
          borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace',
          overflowX: 'auto', marginTop: '8px', border: '1px solid #1f2937',
        }}>{formatted}</pre>
      );
    }
    const parts = msg.content.split(/(\*\*.*?\*\*)/g);
    return (
      <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', fontSize: '15px', color: '#1f2937' }}>
        {parts.map((part, i) => {
          if (part.startsWith('**') && part.endsWith('**')) return <strong key={i} style={{ fontWeight: 700, color: '#111827' }}>{part.slice(2, -2)}</strong>;
          return part;
        })}
      </div>
    );
  };

  const hasInput = input.trim().length > 0;

  /* ================================================================
     STYLES — pixel-perfect match to image copy.png / ui1.png
     ================================================================ */

  /* Outer wrapper: full-height flex column */
  const wrapperStyle = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    minHeight: 0,
    background: '#ffffff',
  };

  /* ── HEADER ── */
  const headerStyle = {
    flexShrink: 0,
    padding: '20px 24px 16px 24px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    borderBottom: '1px solid #e5e7eb',
  };

  /* Robot emoji — using the actual emoji 🤖 to match the reference exactly */
  const emojiStyle = {
    fontSize: '28px',
    lineHeight: 1,
    flexShrink: 0,
  };

  const titleStyle = {
    fontSize: '20px',
    fontWeight: 700,
    color: '#0e7490',          /* teal-blue matching reference */
    lineHeight: 1.2,
    letterSpacing: '-0.01em',
  };

  const subtitleStyle = {
    fontSize: '13px',
    fontWeight: 400,
    color: '#6b7280',
    lineHeight: 1.3,
    marginTop: '2px',
  };

  /* ── MESSAGES AREA ── */
  const messagesAreaStyle = {
    flex: 1,
    minHeight: 0,
    overflowY: 'auto',
    padding: '20px 24px',
    scrollbarWidth: 'thin',
    scrollbarColor: '#cbd5e1 transparent',
  };

  /* Welcome bubble — light cyan/mint, full-width */
  const welcomeBubbleStyle = {
    background: '#e0f7f4',
    borderRadius: '14px',
    padding: '16px 18px',
    fontSize: '15px',
    lineHeight: 1.6,
    color: '#1f2937',
    marginBottom: '16px',
  };

  /* User message — left blue border accent (blockquote style), NOT a blue bubble */
  const userMsgStyle = {
    borderLeft: '4px solid #38bdf8',
    background: '#f0f9ff',
    borderRadius: '0 12px 12px 0',
    padding: '14px 18px',
    fontSize: '15px',
    lineHeight: 1.6,
    color: '#1f2937',
    marginBottom: '12px',
  };

  /* AI regular message — light mint/teal bubble */
  const aiMsgStyle = {
    background: '#e0f7f4',
    borderRadius: '14px',
    padding: '14px 18px',
    fontSize: '15px',
    lineHeight: 1.6,
    color: '#1f2937',
    marginBottom: '12px',
  };

  /* AI success message — light green background */
  const successMsgStyle = {
    background: '#ecfdf5',
    border: '1px solid #a7f3d0',
    borderRadius: '14px',
    padding: '14px 18px',
    fontSize: '15px',
    lineHeight: 1.6,
    color: '#1f2937',
    marginBottom: '12px',
  };

  /* ── INPUT AREA ── */
  const inputAreaStyle = {
    flexShrink: 0,
    padding: '14px 24px 18px 24px',
    borderTop: '1px solid #e5e7eb',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    background: '#ffffff',
  };

  /* Textarea — subtle rounded corners, dark border, no resize handle */
  const textareaStyle = {
    flex: 1,
    minHeight: '44px',
    maxHeight: '100px',
    background: '#ffffff',
    border: '1.5px solid #1a1a1a',
    borderRadius: '8px',
    padding: '11px 16px',
    fontSize: '15px',
    color: '#374151',
    outline: 'none',
    resize: 'none',
    overflow: 'auto',
    lineHeight: 1.4,
    fontFamily: 'inherit',
    transition: 'border-color 0.15s ease',
  };

  /* Log button — rounded rectangle matching reference */
  const logBtnStyle = {
    width: '50px',
    height: '50px',
    borderRadius: '12px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    border: 'none',
    cursor: hasInput ? 'pointer' : 'not-allowed',
    background: hasInput ? '#2563eb' : '#e5e7eb',
    color: hasInput ? '#ffffff' : '#6b7280',
    transition: 'all 0.15s ease',
    flexShrink: 0,
    boxShadow: hasInput ? '0 4px 12px rgba(37, 99, 235, 0.35)' : 'none',
  };

  return (
    <div style={wrapperStyle}>

      {/* ── HEADER ── */}
      <header style={headerStyle}>
        <span style={emojiStyle}>🤖</span>
        <div>
          <div style={titleStyle}>AI Assistant</div>
          <div style={subtitleStyle}>Log Interaction details here via chat</div>
        </div>
      </header>

      {/* ── MESSAGES AREA ── */}
      <div style={messagesAreaStyle}>

        {/* Welcome bubble — always shown when no messages */}
        {chatHistory.length === 0 && (
          <div style={welcomeBubbleStyle}>
            Log interaction details here (e.g., "Met Dr. Smith, discussed Prodo-X efficacy, positive sentiment, shared brochure") or ask for help.
          </div>
        )}

        {/* Chat messages */}
        {chatHistory.map((msg, i) => {
          const isUser = msg.role === 'user';
          const isSuccess = !isUser && isSuccessMessage(msg);

          /* ── User message: left blue accent border (blockquote) ── */
          if (isUser) {
            return (
              <div key={i} style={userMsgStyle}>
                <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{msg.content}</p>
              </div>
            );
          }

          /* ── Success message: green tinted ── */
          if (isSuccess) {
            return (
              <div key={i} style={successMsgStyle}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                  <span style={{ fontSize: '16px', flexShrink: 0, marginTop: '2px' }}>✅</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    {renderMessageContent(msg)}
                    {msg.toolsCalled?.length > 0 && (
                      <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px', paddingTop: '8px', borderTop: '1px solid #d1fae5' }}>
                        {msg.toolsCalled.map((t, j) => (
                          <span key={j} style={{
                            display: 'inline-flex', alignItems: 'center', gap: '4px',
                            background: '#ffffff', color: '#059669', fontSize: '10px',
                            padding: '2px 8px', borderRadius: '999px', fontFamily: 'monospace',
                            border: '1px solid #d1fae5', fontWeight: 600,
                          }}>{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          }

          /* ── Regular AI message: light mint/teal ── */
          return (
            <div key={i} style={aiMsgStyle}>
              {renderMessageContent(msg)}
              {msg.extractedData && Object.keys(msg.extractedData).length > 0 && (
                <pre style={{
                  background: '#111827', color: '#6ee7b7', padding: '12px',
                  borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace',
                  overflowX: 'auto', marginTop: '8px', border: '1px solid #1f2937',
                }}>{JSON.stringify(msg.extractedData, null, 2)}</pre>
              )}
              {msg.toolsCalled?.length > 0 && (
                <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px', paddingTop: '8px', borderTop: '1px solid #b2d8cd' }}>
                  {msg.toolsCalled.map((t, j) => (
                    <span key={j} style={{
                      display: 'inline-flex', alignItems: 'center', gap: '4px',
                      background: '#ffffff', color: '#0891b2', fontSize: '10px',
                      padding: '2px 8px', borderRadius: '999px', fontFamily: 'monospace',
                      border: '1px solid #b2d8cd', fontWeight: 600,
                    }}>{t}</span>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* Loading indicator */}
        {(isStatusPending || isLoading) && (
          <div style={aiMsgStyle}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Loader2 style={{ width: '14px', height: '14px', animation: 'spin 1s linear infinite', color: '#2563eb' }} />
              <span style={{ fontWeight: 600, fontSize: '14px' }}>{isStatusPending ? 'Typing...' : 'Thinking...'}</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── INPUT AREA ── */}
      <div style={inputAreaStyle}>
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
          disabled={isLoading}
          style={textareaStyle}
          onFocus={(e) => { e.target.style.borderColor = '#111827'; }}
          onBlur={(e) => { e.target.style.borderColor = '#1a1a1a'; }}
        />

        {/* Rounded rectangle "A / Log" button */}
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          style={logBtnStyle}
          onMouseEnter={(e) => { if (hasInput) e.currentTarget.style.background = '#1d4ed8'; }}
          onMouseLeave={(e) => { if (hasInput) e.currentTarget.style.background = '#2563eb'; else e.currentTarget.style.background = '#e5e7eb'; }}
        >
          {isLoading ? (
            <div style={{
              width: '16px', height: '16px',
              border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#ffffff',
              borderRadius: '50%', animation: 'spin 0.8s linear infinite',
            }} />
          ) : (
            <>
              <span style={{ fontSize: '18px', fontWeight: 800, lineHeight: 1, marginBottom: '1px' }}>A</span>
              <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', lineHeight: 1 }}>Log</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
