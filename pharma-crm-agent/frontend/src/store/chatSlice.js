import { createSlice } from '@reduxjs/toolkit';

const newThreadId = () => crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36);

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [
      { role: 'ai', content: 'Hello! Describe your HCP interaction and I will log it for you.', toolsCalled: [] },
    ],
    isLoading: false,
    activeTool: null,
    threadId: newThreadId(),
  },
  reducers: {
    addMessage(state, action) {
      state.messages.push(action.payload);
    },
    setLoading(state, action) {
      state.isLoading = action.payload;
    },
    setActiveTool(state, action) {
      state.activeTool = action.payload;
    },
    clearMessages(state) {
      state.messages = [
        { role: 'ai', content: 'Hello! Describe your HCP interaction and I will log it for you.', toolsCalled: [] },
      ];
      state.threadId = newThreadId();
    },
  },
});

export const { addMessage, setLoading, setActiveTool, clearMessages } = chatSlice.actions;
export default chatSlice.reducer;
