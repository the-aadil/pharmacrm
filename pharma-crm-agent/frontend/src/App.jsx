import React from 'react';
import { Provider } from 'react-redux';
import store from './store/store';
import CRMForm from './components/CRMForm';
import AgentChat from './components/AgentChat';

function App() {
  return (
    <Provider store={store}>
      <div className="flex h-screen w-full overflow-hidden font-sans" style={{ background: '#f0f2f5', padding: '8px', gap: '4px' }}>

        {/* Left Panel — CRM Form (CRMForm has its own card wrapper) */}
        <div
          style={{
            flex: '1 1 65%',
            height: '100%',
            minWidth: 0,
            overflow: 'hidden',
          }}
        >
          <CRMForm />
        </div>

        {/* Right Panel — AI Assistant in rounded card */}
        <div
          style={{
            flex: '0 0 34%',
            height: '100%',
            background: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e2e5e9',
            boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <AgentChat />
        </div>

      </div>
    </Provider>
  );
}

export default App;
