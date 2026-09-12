import axios from 'axios';

const api = axios.create({
  baseURL: '/api'
});

export const submitAnalysis = async (problemStatement) => {
  const response = await api.post('/analyze', { problem_statement: problemStatement });
  return response.data;
};

export const getStatus = async (analysisId) => {
  const response = await api.get(`/status/${analysisId}`);
  return response.data;
};

export const getResults = async (analysisId) => {
  const response = await api.get(`/results/${analysisId}`);
  return response.data;
};
