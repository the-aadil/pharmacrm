import { createSlice } from '@reduxjs/toolkit';

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [
      { role: 'ai', content: 'Hello! Describe your HCP interaction and I will log it for you.', toolsCalled: [] },
    ],
    isLoading: false,
    activeTool: null,
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
    },
  },
});

export const { addMessage, setLoading, setActiveTool, clearMessages } = chatSlice.actions;
export default chatSlice.reducer;
