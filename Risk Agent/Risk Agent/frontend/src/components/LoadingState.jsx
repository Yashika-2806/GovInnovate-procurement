import React from 'react';

export default function LoadingState({ status }) {
  const progress = status?.progress || 0;
  const currentStep = status?.current_step || 'Initializing...';
  
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 max-w-lg mx-auto w-full">
      <div className="mb-8 relative w-32 h-32 flex items-center justify-center">
        <svg className="animate-spin text-blue-500 w-16 h-16" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      
      <h3 className="text-2xl font-bold mb-2 text-white text-center">Evaluating Startup Risk</h3>
      <p className="text-gray-400 mb-8 text-center h-6">{currentStep}</p>
      
      <div className="w-full bg-gray-800 rounded-full h-3 mb-2 overflow-hidden border border-gray-700">
        <div 
          className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="w-full text-right text-xs text-gray-500 font-mono">
        {Math.round(progress)}%
      </div>
    </div>
  );
}
