import React from 'react';
import { Provider } from 'react-redux';
import store from './store/store';
import CRMForm from './components/CRMForm';
import AgentChat from './components/AgentChat';

function App() {
  return (
    <Provider store={store}>
      <div className="flex h-screen w-full bg-[#f8f9fa] overflow-hidden font-sans">
        {/* Left Panel - Clean White Card */}
        <div className="w-[65%] p-6 overflow-y-auto h-full flex justify-center">
          <div className="w-full max-w-5xl h-[calc(100vh-3rem)]">
            <CRMForm />
          </div>
        </div>
        {/* Right Panel - Clean Border */}
        <div className="w-[35%] bg-white border-l border-gray-200 shadow-xl flex flex-col h-full">
          <AgentChat />
        </div>
      </div>
    </Provider>
  );
}

export default App;
