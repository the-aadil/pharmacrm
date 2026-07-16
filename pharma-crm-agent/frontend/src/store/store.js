import { configureStore } from '@reduxjs/toolkit';
import formReducer from './formSlice';
import chatReducer from './chatSlice';

const store = configureStore({
  reducer: {
    form: formReducer,
    chat: chatReducer,
  },
});

export default store;
