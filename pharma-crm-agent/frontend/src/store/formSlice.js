import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  fields: {
    hcp_name: '',
    interaction_type: 'visit',
    date: '',
    time: '',
    attendees: '',
    duration_minutes: 30,
    topics_discussed: '',
    sentiment: 'neutral',
    outcomes: '',
    next_steps: '',
    products: [],
    follow_ups: [],
    ai_summary: '',
  },
  complianceFlag: false,
  complianceNotes: '',
  status: 'idle',
  isStatusPending: false,
  interactionId: null,
  currentRecord: null,
  briefing: null,
  suggestions: null,
  followUps: [],
  searchResults: [],
  isLoadingBriefing: false,
  isLoadingSuggestions: false,
  isLoadingFollowUps: false,
  isLoadingSearch: false,
};

const formSlice = createSlice({
  name: 'form',
  initialState,
  reducers: {
    setFormField(state, action) {
      const { key, value } = action.payload;
      state.fields[key] = value;
    },
    populateFromAI(state, action) {
      const data = action.payload;
      if (data.hcp_name !== undefined) state.fields.hcp_name = data.hcp_name;
      if (data.interaction_type !== undefined) state.fields.interaction_type = data.interaction_type;
      if (data.date !== undefined) state.fields.date = data.date;
      if (data.time !== undefined) state.fields.time = data.time;
      if (data.attendees !== undefined) state.fields.attendees = data.attendees;
      if (data.duration_minutes !== undefined) state.fields.duration_minutes = data.duration_minutes;
      if (data.topics_discussed !== undefined) state.fields.topics_discussed = data.topics_discussed;
      if (data.sentiment !== undefined) state.fields.sentiment = data.sentiment;
      if (data.outcomes !== undefined) state.fields.outcomes = data.outcomes;
      if (data.next_steps !== undefined) state.fields.next_steps = data.next_steps;
      if (data.products !== undefined) state.fields.products = data.products;
      if (data.follow_ups !== undefined) state.fields.follow_ups = data.follow_ups;
      if (data.ai_summary !== undefined) state.fields.ai_summary = data.ai_summary;
      if (data.compliance_flag !== undefined) state.complianceFlag = data.compliance_flag;
      if (data.compliance_notes !== undefined) state.complianceNotes = data.compliance_notes;
    },
    setStatus(state, action) {
      state.status = action.payload;
    },
    setInteractionId(state, action) {
      state.interactionId = action.payload;
    },
    setCurrentRecord(state, action) {
      state.currentRecord = action.payload;
    },
    setBriefing(state, action) {
      state.briefing = action.payload;
    },
    setSuggestions(state, action) {
      state.suggestions = action.payload;
    },
    setFollowUps(state, action) {
      state.followUps = action.payload;
    },
    setSearchResults(state, action) {
      state.searchResults = action.payload;
    },
    setIsLoadingBriefing(state, action) {
      state.isLoadingBriefing = action.payload;
    },
    setIsLoadingSuggestions(state, action) {
      state.isLoadingSuggestions = action.payload;
    },
    setIsLoadingFollowUps(state, action) {
      state.isLoadingFollowUps = action.payload;
    },
    setIsLoadingSearch(state, action) {
      state.isLoadingSearch = action.payload;
    },
    addFollowUp(state, action) {
      state.followUps.push(action.payload);
    },
    setIsStatusPending(state, action) {
      state.isStatusPending = action.payload;
    },
    resetForm(state) {
      Object.assign(state, initialState);
    },
  },
});

export const { 
  setFormField, 
  populateFromAI, 
  setStatus, 
  setIsStatusPending,
  setInteractionId, 
  setCurrentRecord,
  setBriefing,
  setSuggestions,
  setFollowUps,
  setSearchResults,
  setIsLoadingBriefing,
  setIsLoadingSuggestions,
  setIsLoadingFollowUps,
  setIsLoadingSearch,
  addFollowUp,
  resetForm 
} = formSlice.actions;
export default formSlice.reducer;
