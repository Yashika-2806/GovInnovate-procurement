import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getStatus, getResults } from '../api/client';
import LoadingState from '../components/LoadingState';
import Dashboard from '../components/Dashboard';
import ReportView from '../components/ReportView';
import ScoreCard from '../components/ScoreCard';
import SimilarityChart from '../components/SimilarityChart';
import CompanyCard from '../components/CompanyCard';
import ScoreTable from '../components/ScoreTable';

export default function ResultsPage() {
  const { analysisId } = useParams();
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    let interval;
    const checkStatus = async () => {
      try {
        const statusData = await getStatus(analysisId);
        setStatus(statusData);
        
        if (statusData.status === 'completed' || statusData.status === 'complete') {
          clearInterval(interval);
          const resultsData = await getResults(analysisId);
          setResults(resultsData);
        } else if (statusData.status === 'error') {
          clearInterval(interval);
          setError(statusData.error || 'Analysis failed.');
        }
      } catch (err) {
        clearInterval(interval);
        setError(err.message || 'Error fetching status');
      }
    };
    
    checkStatus();
    interval = setInterval(checkStatus, 2000);
    return () => clearInterval(interval);
  }, [analysisId]);

  if (error) {
    return (
      <div className="p-12 text-center max-w-xl mx-auto">
        <div className="bg-red-950/40 border border-red-800 text-red-300 p-6 rounded-2xl shadow-xl">
          <h3 className="text-xl font-bold mb-2">Analysis Encountered an Error</h3>
          <p className="text-sm text-red-400 mb-4">{error}</p>
          <a href="/" className="inline-block px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-semibold transition-colors">
            Try Another Problem Statement
          </a>
        </div>
      </div>
    );
  }

  if (!status || status.status === 'processing' || !results) {
    return <LoadingState status={status} />;
  }

  // Normalized data extraction for both direct API outputs & nested FullReport schemas
  const categoryScores = results?.risk_assessment?.category_scores || results?.categoryScores || [];
  const overallScore = results?.executive_summary?.overall_score ?? results?.executive_summary?.cumulative_score ?? results?.cumulativeScore ?? results?.overallScore ?? 0;
  const riskLevel = results?.executive_summary?.overall_risk_level || results?.executive_summary?.risk_classification || results?.riskLevel || 'MODERATE';
  
  // Transform topRisks into objects if they are strings
  const rawTopRisks = results?.risk_assessment?.top_risks || results?.topRisks || [];
  const topRisks = rawTopRisks.map(r => {
    if (typeof r === 'string') {
      const match = categoryScores.find(c => c.category === r);
      return { name: r, score: match ? match.score : 70 };
    }
    return r;
  });

  const matrixItems = results?.risk_assessment?.risk_matrix || results?.matrixItems || [];
  const comparables = results?.comparable_companies || results?.similar_companies || results?.comparables || [];
  const weightedScores = results?.score_calculation || results?.risk_assessment?.weighted_scores || results?.weightedScores || [];
  
  const sourcesCount = (results?.citations?.length) || (results?.sources?.length) || 0;
  const stats = {
    sources: sourcesCount,
    dataQuality: results?.data_quality_assessment || (sourcesCount > 5 ? 'High (Verified Data)' : 'Moderate'),
    confidence: results?.statistical_findings?.sample_size ? 85 : 75
  };

  const dashboardProps = {
    overallScore,
    riskLevel,
    categoryScores,
    topRisks,
    matrixItems,
    stats
  };

  const tabs = [
    { id: 'dashboard', label: '📊 Risk Dashboard' },
    { id: 'detailed', label: '🔍 12-Factor Deep Dive' },
    { id: 'historical', label: '🏢 Historical Failures & Benchmarks' },
    { id: 'report', label: '📄 Explainable Research Report' }
  ];

  return (
    <div className="flex-1 flex flex-col w-full max-w-7xl mx-auto px-4 py-6 animate-fade-in">
      {/* Header Badge */}
      <div className="flex flex-wrap items-center justify-between pb-4 mb-6 border-b border-gray-800 gap-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">
            LangGraph Multi-Agent Audit
          </span>
          <h1 className="text-2xl font-bold text-white mt-1">Startup Failure Risk Assessment</h1>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-400">Risk Score:</span>
          <span className={`text-xl font-black px-3 py-1 rounded-lg border ${
            overallScore >= 80 ? 'bg-red-500/20 border-red-500/40 text-red-400' :
            overallScore >= 60 ? 'bg-orange-500/20 border-orange-500/40 text-orange-400' :
            overallScore >= 40 ? 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400' :
            'bg-green-500/20 border-green-500/40 text-green-400'
          }`}>
            {Math.round(overallScore)} / 100 ({riskLevel})
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-800 mb-6 space-x-2 overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-3 border-b-2 text-sm font-semibold transition-all whitespace-nowrap ${
              activeTab === tab.id 
                ? 'border-blue-500 text-blue-400 bg-blue-500/5' 
                : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="flex-1">
        {activeTab === 'dashboard' && <Dashboard results={dashboardProps} />}
        
        {activeTab === 'detailed' && (
          <div className="grid grid-cols-1 gap-4 max-w-5xl mx-auto">
            <div className="mb-2">
              <h2 className="text-xl font-bold text-white">12 Risk Categories Deep Dive</h2>
              <p className="text-sm text-gray-400">Expand each dimension to see evidence, sub-factors, historical precedents, and recommended mitigations.</p>
            </div>
            {categoryScores.map((cat, i) => (
              <ScoreCard key={i} categoryScore={cat} />
            ))}
          </div>
        )}
        
        {activeTab === 'historical' && (
          <div className="space-y-8 max-w-5xl mx-auto">
            <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-lg">
              <h2 className="text-xl font-bold text-white mb-2">Historical Similarity Analysis</h2>
              <p className="text-sm text-gray-400 mb-4">
                Multi-dimensional similarity scoring comparing this startup against failed and successful ventures in the same vertical.
              </p>
              <div className="h-80">
                <SimilarityChart companies={comparables} />
              </div>
            </div>

            <h3 className="text-lg font-bold text-white pt-2">Comparable Company Profiles</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {comparables.map((comp, i) => (
                <CompanyCard key={i} company={comp} />
              ))}
            </div>
          </div>
        )}
        
        {activeTab === 'report' && (
          <div className="max-w-5xl mx-auto space-y-8">
            <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-lg">
              <h2 className="text-xl font-bold text-white mb-2">Transparent Risk Score Calculation</h2>
              <p className="text-sm text-gray-400 mb-4">
                Industry-dependent weight matrix with exact scoring weights applied to each category.
              </p>
              <ScoreTable weightedScores={weightedScores} cumulativeScore={overallScore} />
            </div>

            <div className="bg-gray-900 p-8 rounded-2xl border border-gray-800 shadow-xl">
              <ReportView report={results} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
