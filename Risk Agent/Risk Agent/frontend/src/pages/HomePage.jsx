import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitAnalysis } from '../api/client';

export default function HomePage() {
  const [problemStatement, setProblemStatement] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleAnalyze = async () => {
    if (!problemStatement.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { analysis_id } = await submitAnalysis(problemStatement);
      navigate(`/results/${analysis_id}`);
    } catch (err) {
      setError(err.message || 'Error submitting analysis');
      setLoading(false);
    }
  };

  const chips = [
    "Uber for dog walking",
    "AI-powered legal assistant",
    "B2B SaaS for construction",
    "Direct-to-consumer sustainable sneakers"
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center max-w-3xl mx-auto w-full">
      <h1 className="text-4xl md:text-5xl font-extrabold mb-4">
        AI Startup Risk Evaluator
      </h1>
      <p className="text-xl text-gray-400 mb-8">
        Research-backed, data-driven startup failure risk assessment
      </p>
      
      <div className="w-full bg-gray-900 rounded-xl p-4 border border-gray-800 shadow-xl mb-4">
        <textarea
          className="w-full h-40 bg-gray-950 text-white p-4 rounded-lg border border-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none"
          placeholder="Describe your startup idea, target market, and business model..."
          value={problemStatement}
          onChange={(e) => setProblemStatement(e.target.value)}
        />
      </div>

      <div className="flex flex-wrap gap-2 justify-center mb-8">
        {chips.map(chip => (
          <button
            key={chip}
            onClick={() => setProblemStatement(chip)}
            className="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-sm rounded-full text-gray-300 transition-colors"
          >
            {chip}
          </button>
        ))}
      </div>

      {error && <p className="text-red-400 mb-4">{error}</p>}

      <button
        onClick={handleAnalyze}
        disabled={loading || !problemStatement.trim()}
        className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:opacity-50 text-white font-bold rounded-lg text-lg transition-all shadow-lg shadow-purple-900/20"
      >
        {loading ? 'Submitting...' : 'Analyze Risk'}
      </button>
    </div>
  );
}
