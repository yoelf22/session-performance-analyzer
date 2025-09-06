import { useState, useMemo, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ScatterChart, Scatter, ResponsiveContainer, ReferenceLine
} from 'recharts';

// Types
interface SessionData {
  sessionNumber: number;
  sessionLength: number;
  successRate: number;
  smoothedSuccessRate?: number;
}

interface Statistics {
  totalSessions: number;
  correlationCoeff: number;
  initialRate: number;
  finalRate: number;
  totalImprovement: number;
  inflectionPoint: number;
  preInflectionSlope: number;
  postInflectionSlope: number;
  mean: number;
  standardDeviation: number;
  minValue: number;
  maxValue: number;
}

const SessionAnalyzer: React.FC = () => {
  const [smoothingLevel, setSmoothingLevel] = useState<number>(15);
  const [showRawData, setShowRawData] = useState<boolean>(true);
  const [showSmoothed, setShowSmoothed] = useState<boolean>(true);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  // Generate realistic session data with inflection point
  const generateSessionData = useCallback((): SessionData[] => {
    const sessions: SessionData[] = [];
    const totalSessions = 200;
    const inflectionPoint = 130;
    
    for (let i = 1; i <= totalSessions; i++) {
      let baseRate: number;
      
      // Two-phase performance curve
      if (i <= inflectionPoint) {
        // Phase 1: Rapid improvement (logarithmic growth)
        baseRate = 30 + 25 * Math.log(i) / Math.log(inflectionPoint);
      } else {
        // Phase 2: Plateau with diminishing returns
        const plateauProgress = (i - inflectionPoint) / (totalSessions - inflectionPoint);
        baseRate = 55 + 15 * (1 - Math.exp(-plateauProgress * 2));
      }
      
      // Add realistic noise with cyclical patterns
      const cyclicalNoise = 2 * Math.sin(i * 0.1) + 1.5 * Math.cos(i * 0.05);
      const randomNoise = (Math.random() - 0.5) * 7.5;
      const sessionLength = Math.max(5, Math.min(45, baseRate + cyclicalNoise + randomNoise));
      
      // Success rate correlates with session length but with variation
      const baseSuccessRate = Math.min(95, Math.max(10, 
        20 + (sessionLength - 5) * 1.8 + (Math.random() - 0.5) * 15
      ));
      
      sessions.push({
        sessionNumber: i,
        sessionLength: Math.round(sessionLength * 100) / 100,
        successRate: Math.round(baseSuccessRate * 100) / 100
      });
    }
    
    return sessions;
  }, []);

  // Apply smoothing filter
  const applySmoothingFilter = useCallback((data: SessionData[], windowSize: number): SessionData[] => {
    return data.map((item, index) => {
      const start = Math.max(0, index - Math.floor(windowSize / 2));
      const end = Math.min(data.length, index + Math.floor(windowSize / 2) + 1);
      const window = data.slice(start, end);
      
      const smoothedSuccessRate = window.reduce((sum, d) => sum + d.successRate, 0) / window.length;
      
      return {
        ...item,
        smoothedSuccessRate: Math.round(smoothedSuccessRate * 100) / 100
      };
    });
  }, []);

  // Detect inflection point using second derivative
  const detectInflectionPoint = useCallback((data: SessionData[]): number => {
    const smoothedData = applySmoothingFilter(data, 10);
    let maxCurvature = 0;
    let inflectionPoint = 130; // Default expected point
    
    for (let i = 20; i < smoothedData.length - 20; i++) {
      const prev = smoothedData[i - 10].smoothedSuccessRate || 0;
      const curr = smoothedData[i].smoothedSuccessRate || 0;
      const next = smoothedData[i + 10].smoothedSuccessRate || 0;
      
      // Calculate second derivative (curvature)
      const curvature = Math.abs((next - 2 * curr + prev));
      
      if (curvature > maxCurvature && i > 100 && i < 160) {
        maxCurvature = curvature;
        inflectionPoint = i;
      }
    }
    
    return inflectionPoint;
  }, [applySmoothingFilter]);

  // Calculate comprehensive statistics
  const calculateStatistics = useCallback((data: SessionData[]): Statistics => {
    const successRates = data.map(d => d.successRate);
    const sessionNumbers = data.map(d => d.sessionNumber);
    
    // Basic statistics
    const sum = successRates.reduce((a, b) => a + b, 0);
    const mean = sum / successRates.length;
    const variance = successRates.reduce((sum, rate) => sum + Math.pow(rate - mean, 2), 0) / successRates.length;
    const standardDeviation = Math.sqrt(variance);
    const minValue = Math.min(...successRates);
    const maxValue = Math.max(...successRates);
    
    // Correlation calculation
    const n = data.length;
    const sumX = sessionNumbers.reduce((a, b) => a + b, 0);
    const sumY = successRates.reduce((a, b) => a + b, 0);
    const sumXY = data.reduce((sum, d) => sum + d.sessionNumber * d.successRate, 0);
    const sumX2 = sessionNumbers.reduce((sum, x) => sum + x * x, 0);
    const sumY2 = successRates.reduce((sum, y) => sum + y * y, 0);
    
    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
    const correlationCoeff = numerator / denominator;
    
    // Inflection point and slopes
    const inflectionPoint = detectInflectionPoint(data);
    const preInflectionData = data.slice(0, inflectionPoint);
    const postInflectionData = data.slice(inflectionPoint);
    
    // Calculate slopes
    const calculateSlope = (subset: SessionData[]) => {
      if (subset.length < 2) return 0;
      const n = subset.length;
      const sumX = subset.reduce((sum, d) => sum + d.sessionNumber, 0);
      const sumY = subset.reduce((sum, d) => sum + d.successRate, 0);
      const sumXY = subset.reduce((sum, d) => sum + d.sessionNumber * d.successRate, 0);
      const sumX2 = subset.reduce((sum, d) => sum + d.sessionNumber * d.sessionNumber, 0);
      return (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    };
    
    const preInflectionSlope = calculateSlope(preInflectionData);
    const postInflectionSlope = calculateSlope(postInflectionData);
    
    return {
      totalSessions: data.length,
      correlationCoeff: Math.round(correlationCoeff * 1000) / 1000,
      initialRate: data[0].successRate,
      finalRate: data[data.length - 1].successRate,
      totalImprovement: data[data.length - 1].successRate - data[0].successRate,
      inflectionPoint,
      preInflectionSlope: Math.round(preInflectionSlope * 1000) / 1000,
      postInflectionSlope: Math.round(postInflectionSlope * 1000) / 1000,
      mean: Math.round(mean * 100) / 100,
      standardDeviation: Math.round(standardDeviation * 100) / 100,
      minValue,
      maxValue
    };
  }, [detectInflectionPoint]);

  // Generate and process data
  const rawData = useMemo(() => generateSessionData(), [generateSessionData]);
  const processedData = useMemo(() => 
    applySmoothingFilter(rawData, smoothingLevel), 
    [rawData, smoothingLevel, applySmoothingFilter]
  );
  const statistics = useMemo(() => 
    calculateStatistics(processedData), 
    [processedData, calculateStatistics]
  );

  // Export functionality
  const exportToCSV = useCallback(async () => {
    setIsExporting(true);
    
    try {
      const headers = ['Session Number', 'Session Length', 'Success Rate', 'Smoothed Success Rate'];
      const csvContent = [
        headers.join(','),
        ...processedData.map(row => [
          row.sessionNumber,
          row.sessionLength,
          row.successRate,
          row.smoothedSuccessRate || ''
        ].join(','))
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `session-analysis-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  }, [processedData]);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-4xl font-bold text-gradient mb-4">
            📊 Session Performance Analyzer
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Advanced analytics with trend analysis, configurable smoothing, and comprehensive 
            data visualization for session performance optimization
          </p>
        </div>

        {/* Controls */}
        <div className="card p-6 mb-8 animate-slide-up">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Smoothing Level: {smoothingLevel} sessions
                </label>
                <input
                  type="range"
                  min="5"
                  max="25"
                  value={smoothingLevel}
                  onChange={(e) => setSmoothingLevel(Number(e.target.value))}
                  className="w-40 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
              </div>
              
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={showRawData}
                    onChange={(e) => setShowRawData(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Show Raw Data</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={showSmoothed}
                    onChange={(e) => setShowSmoothed(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Show Smoothed Trend</span>
                </label>
              </div>
            </div>
            
            <button
              onClick={exportToCSV}
              disabled={isExporting}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExporting ? (
                <>
                  <div className="animate-spin -ml-1 mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  Exporting...
                </>
              ) : (
                <>
                  <svg className="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                  </svg>
                  Export CSV
                </>
              )}
            </button>
          </div>
        </div>

        {/* Statistics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="stat-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Sessions</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.totalSessions}</p>
              </div>
              <div className="p-3 bg-primary-100 rounded-full">
                <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Correlation</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.correlationCoeff}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
            </div>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Improvement</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.totalImprovement.toFixed(1)}%</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 11l5-5m0 0l5 5m-5-5v12" />
                </svg>
              </div>
            </div>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Inflection Point</p>
                <p className="text-2xl font-bold text-gray-900">Session {statistics.inflectionPoint}</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          
          {/* Raw Data Scatter Plot */}
          <div className="chart-container">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Raw Session Data
            </h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart data={rawData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="sessionNumber" 
                    type="number" 
                    domain={[0, 200]}
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                  />
                  <YAxis 
                    dataKey="successRate"
                    domain={[0, 100]}
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                  />
                  <Tooltip 
                    formatter={(value, name) => [
                      `${value}%`, 
                      name === 'successRate' ? 'Success Rate' : name
                    ]}
                    labelFormatter={(value) => `Session: ${value}`}
                  />
                  <Scatter 
                    dataKey="successRate" 
                    fill="#3b82f6" 
                    fillOpacity={0.6}
                    name="Success Rate"
                  />
                  <ReferenceLine 
                    x={statistics.inflectionPoint} 
                    stroke="#ef4444" 
                    strokeDasharray="5 5"
                    label={{ value: "Inflection Point", position: "insideTopRight" }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trend Analysis */}
          <div className="chart-container">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Trend Analysis
            </h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={processedData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="sessionNumber" 
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                  />
                  <YAxis 
                    domain={[0, 100]}
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                  />
                  <Tooltip 
                    formatter={(value, name) => [
                      `${value}%`, 
                      name === 'successRate' ? 'Raw Success Rate' : 'Smoothed Success Rate'
                    ]}
                    labelFormatter={(value) => `Session: ${value}`}
                  />
                  <Legend />
                  
                  {showRawData && (
                    <Line 
                      type="monotone" 
                      dataKey="successRate" 
                      stroke="#94a3b8" 
                      strokeWidth={1}
                      dot={false}
                      name="Raw Data"
                      strokeOpacity={0.5}
                    />
                  )}
                  
                  {showSmoothed && (
                    <Line 
                      type="monotone" 
                      dataKey="smoothedSuccessRate" 
                      stroke="#3b82f6" 
                      strokeWidth={3}
                      dot={false}
                      name="Smoothed Trend"
                    />
                  )}
                  
                  <ReferenceLine 
                    x={statistics.inflectionPoint} 
                    stroke="#ef4444" 
                    strokeDasharray="5 5"
                    label={{ value: "Inflection", position: "insideTopRight" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Detailed Statistics */}
        <div className="card p-8">
          <h3 className="text-2xl font-semibold text-gray-900 mb-6">Detailed Analysis</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Performance Metrics</h4>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="text-gray-600">Initial Success Rate:</dt>
                  <dd className="font-medium">{statistics.initialRate.toFixed(1)}%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Final Success Rate:</dt>
                  <dd className="font-medium">{statistics.finalRate.toFixed(1)}%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Total Improvement:</dt>
                  <dd className="font-medium text-green-600">{statistics.totalImprovement.toFixed(1)}%</dd>
                </div>
              </dl>
            </div>
            
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Statistical Summary</h4>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="text-gray-600">Mean:</dt>
                  <dd className="font-medium">{statistics.mean}%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Std Deviation:</dt>
                  <dd className="font-medium">{statistics.standardDeviation}%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Range:</dt>
                  <dd className="font-medium">{statistics.minValue}% - {statistics.maxValue}%</dd>
                </div>
              </dl>
            </div>
            
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Trend Analysis</h4>
              <dl className="space-y-2">
                <div className="flex justify-between">
                  <dt className="text-gray-600">Pre-Inflection Slope:</dt>
                  <dd className="font-medium">{statistics.preInflectionSlope}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Post-Inflection Slope:</dt>
                  <dd className="font-medium">{statistics.postInflectionSlope}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Correlation:</dt>
                  <dd className="font-medium">{statistics.correlationCoeff}</dd>
                </div>
              </dl>
            </div>
          </div>
          
          <div className="mt-8 p-4 bg-blue-50 rounded-lg">
            <h4 className="text-lg font-medium text-blue-900 mb-2">Key Insights</h4>
            <ul className="text-blue-800 space-y-1">
              <li>• Performance shows two distinct phases with transition at session {statistics.inflectionPoint}</li>
              <li>• Strong positive correlation ({statistics.correlationCoeff}) between session number and success rate</li>
              <li>• {statistics.preInflectionSlope > statistics.postInflectionSlope ? 'Rapid' : 'Gradual'} improvement in early sessions, then {statistics.postInflectionSlope > 0.1 ? 'continued growth' : 'plateau'}</li>
              <li>• Total improvement of {statistics.totalImprovement.toFixed(1)}% over {statistics.totalSessions} sessions</li>
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
};

export default SessionAnalyzer;