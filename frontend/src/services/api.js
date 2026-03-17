import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Send a message to the chat API.
 * @param {string} message - User message text
 * @param {string} [conversationId] - Optional conversation UUID for continuity
 * @returns {Promise<{ success: boolean, response?: string, conversation_id?: string, timestamp?: string, error?: string }>}
 */
export const sendMessage = async (message, conversationId = null) => {
  const payload = { message };
  if (conversationId) payload.conversation_id = conversationId;
  const response = await axios.post(`${API_BASE_URL}/api/chat/`, payload);
  return response.data;
};
