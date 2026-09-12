import React from 'react';
import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <header className="border-b border-gray-800 bg-gray-900 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Risk Evaluator AI
            </h1>
            <p className="text-sm text-gray-400">Startup failure risk assessment</p>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 flex flex-col">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/results/:analysisId" element={<ResultsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
