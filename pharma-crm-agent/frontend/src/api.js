import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

export async function sendMessage(message, threadId = 'default') {
  try {
    const { data } = await api.post('/api/chat', { message, thread_id: threadId });
    return data;
  } catch (err) {
    return { status: 'error', reply: err.message, extracted_data: {}, tools_called: [] };
  }
}

export async function confirmInteraction(recordData) {
  try {
    const recordJson = typeof recordData === 'string' ? recordData : JSON.stringify(recordData);
    const { data } = await api.post('/api/interactions/confirm', { record_json: recordJson });
    return data;
  } catch (err) {
    return { status: 'error', message: err.message };
  }
}

export async function editInteraction(interactionId, changeRequest) {
  try {
    const { data } = await api.put(`/api/interactions/${interactionId}`, {
      interaction_id: interactionId,
      change_request: changeRequest,
    });
    return data;
  } catch (err) {
    return { status: 'error', message: err.message };
  }
}

export async function searchHCPs(query) {
  try {
    const { data } = await api.get('/api/hcps', { params: { query } });
    return data;
  } catch (err) {
    return { status: 'error', message: err.message };
  }
}

export async function getHCPBriefing(hcpName) {
  try {
    const { data } = await api.get(`/api/hcps/${encodeURIComponent(hcpName)}/briefing`);
    return data;
  } catch (err) {
    return { status: 'error', message: err.message };
  }
}

export async function getSuggestions(hcpName) {
  try {
    const { data } = await api.get(`/api/hcps/${encodeURIComponent(hcpName)}/suggestions`);
    return data;
  } catch (err) {
    return { status: 'error', message: err.message };
  }
}

export async function scheduleFollowUp(hcpName, dueDescription, note) {
  try {
    const { data } = await api.post('/api/followups', {
      hcp_name: hcpName,
      due_description: dueDescription,
      note,
    });
    return data;
  } catch (err) {
    return { status: 'error', message: err.message };
  }
}

export default api;
