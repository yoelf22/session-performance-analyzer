import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { BarChart3, TrendingDown, AlertTriangle, Upload, Download } from 'lucide-react';

interface DataPoint {
  sessionNumber: number;
  sessionLength: number;
  successRate: number;
}

const SessionAnalyzer: React.FC = () => {
  const [data, setData] = useState<DataPoint[]>([]);
  const [viewMode, setViewMode] = useState<'raw' | 'trend'>('raw');
  const [smoothingLevel, setSmoothingLevel] = useState<number>(10);
  const [stats, setStats] = useState({
    totalSessions: 0,
    inflectionPoint: '0',
    earlySuccessRate: '0',
    lateSuccessRate: '0',
  });
  const [isUsingCustomData, setIsUsingCustomData] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Load sample data by default on first render
    if (data.length === 0) {
      const sampleData = generateSampleData();
      setData(sampleData);
      setIsUsingCustomData(false);
      setUploadStatus('idle');
      
      const earlyData = sampleData.slice(0, 130);
      const lateData = sampleData.slice(130);
      const inflectionPoint = 1.0 + (130 - 1) * 0.2;
      
      setStats({
        totalSessions: sampleData.length,
        inflectionPoint: inflectionPoint.toFixed(1),
        earlySuccessRate: (earlyData.reduce((sum, p) => sum + p.successRate, 0) / earlyData.length).toFixed(1),
        lateSuccessRate: (lateData.reduce((sum, p) => sum + p.successRate, 0) / lateData.length).toFixed(1),
      });
    }
  }, []);

  const generateSampleData = (): DataPoint[] => {
    const points: DataPoint[] = [];
    for (let i = 1; i <= 200; i++) {
      const sessionLength = 1.0 + (i - 1) * 0.2;
      let baseSuccessRate: number;
      
      if (i <= 130) {
        const progressRatio = (i - 1) / 129;
        const curveValue = 1 - Math.pow(progressRatio, 0.7);
        baseSuccessRate = 0.55 + (0.99 - 0.55) * curveValue;
      } else {
        baseSuccessRate = 0.05;
      }
      
      const noise = (Math.random() - 0.5) * 0.2;
      const successRate = Math.max(0, Math.min(1, baseSuccessRate + noise));
      
      points.push({
        sessionNumber: i,
        sessionLength: Number(sessionLength.toFixed(2)),
        successRate: Number((successRate * 100).toFixed(2)),
      });
    }
    return points;
  };

  const getSmoothedData = (): DataPoint[] => {
    if (!data.length) return [];
    
    const smoothed: DataPoint[] = [];
    for (let i = 0; i < data.length; i += smoothingLevel) {
      const chunk = data.slice(i, i + smoothingLevel);
      if (chunk.length === 0) continue;
      
      const avgLength = chunk.reduce((sum, p) => sum + p.sessionLength, 0) / chunk.length;
      const avgSuccess = chunk.reduce((sum, p) => sum + p.successRate, 0) / chunk.length;
      
      smoothed.push({
        sessionNumber: Math.round(i + smoothingLevel / 2),
        sessionLength: Number(avgLength.toFixed(2)),
        successRate: Number(avgSuccess.toFixed(2)),
      });
    }
    return smoothed;
  };

  const parseCSV = (csvText: string): DataPoint[] => {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('CSV must have at least a header row and one data row');
    }
    
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const data: DataPoint[] = [];
    
    // Find column indices
    const sessionNumIndex = headers.findIndex(h => 
      h.includes('session') && (h.includes('number') || h.includes('num') || h.includes('id'))
    );
    const sessionLengthIndex = headers.findIndex(h => 
      h.includes('session') && (h.includes('length') || h.includes('duration') || h.includes('time'))
    );
    const successRateIndex = headers.findIndex(h => 
      h.includes('success') && (h.includes('rate') || h.includes('percent') || h.includes('%'))
    );
    
    if (sessionNumIndex === -1 || sessionLengthIndex === -1 || successRateIndex === -1) {
      throw new Error('CSV must contain columns for session number, session length, and success rate');
    }
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      if (values.length < 3) continue;
      
      const sessionNumber = parseInt(values[sessionNumIndex]);
      const sessionLength = parseFloat(values[sessionLengthIndex]);
      const successRate = parseFloat(values[successRateIndex]);
      
      if (!isNaN(sessionNumber) && !isNaN(sessionLength) && !isNaN(successRate)) {
        data.push({
          sessionNumber,
          sessionLength,
          successRate: successRate > 1 ? successRate : successRate * 100 // Handle both 0.85 and 85% formats
        });
      }
    }
    
    if (data.length === 0) {
      throw new Error('No valid data rows found in CSV');
    }
    
    // Sort by session number
    return data.sort((a, b) => a.sessionNumber - b.sessionNumber);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadStatus('error');
      alert('Please upload a CSV file');
      return;
    }
    
    setUploadStatus('uploading');
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const csvText = String(e.target?.result ?? '');
        const parsedData = parseCSV(csvText);
        
        setData(parsedData);
        setIsUsingCustomData(true);
        setUploadStatus('success');
        
        // Calculate stats for uploaded data
        const earlyData = parsedData.slice(0, Math.floor(parsedData.length * 0.65));
        const lateData = parsedData.slice(Math.floor(parsedData.length * 0.65));
        const inflectionPoint = parsedData.length > 0 ? parsedData[Math.floor(parsedData.length * 0.65)]?.sessionLength || 0 : 0;
        
        setStats({
          totalSessions: parsedData.length,
          inflectionPoint: inflectionPoint.toFixed(1),
          earlySuccessRate: earlyData.length > 0 ? (earlyData.reduce((sum, p) => sum + p.successRate, 0) / earlyData.length).toFixed(1) : '0',
          lateSuccessRate: lateData.length > 0 ? (lateData.reduce((sum, p) => sum + p.successRate, 0) / lateData.length).toFixed(1) : '0',
        });
        
        alert(`Successfully loaded ${parsedData.length} data points from ${file.name}`);
      } catch (error) {
        console.error('Error parsing CSV:', error);
        setUploadStatus('error');
        alert(`Error parsing CSV: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    };
    
    reader.onerror = () => {
      setUploadStatus('error');
      alert('Error reading file');
    };
    
    reader.readAsText(file);
  };

  const loadSampleData = () => {
    const sampleData = generateSampleData();
    setData(sampleData);
    setIsUsingCustomData(false);
    setUploadStatus('idle');
    
    const earlyData = sampleData.slice(0, 130);
    const lateData = sampleData.slice(130);
    const inflectionPoint = 1.0 + (130 - 1) * 0.2;
    
    setStats({
      totalSessions: sampleData.length,
      inflectionPoint: inflectionPoint.toFixed(1),
      earlySuccessRate: (earlyData.reduce((sum, p) => sum + p.successRate, 0) / earlyData.length).toFixed(1),
      lateSuccessRate: (lateData.reduce((sum, p) => sum + p.successRate, 0) / lateData.length).toFixed(1),
    });
  };

  const exportData = () => {
    const csvContent = [
      'Session Number,Session Length,Success Rate',
      ...data.map(row => `${row.sessionNumber},${row.sessionLength},${row.successRate}`)
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'session_analysis_results.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const StatCard = ({ title, value, icon: Icon, color }: any) => (
    <div className={`bg-white rounded-xl p-6 shadow-lg border-l-4 ${color}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <Icon className="h-8 w-8 text-gray-400" />
      </div>
    </div>
  );

  const renderChart = () => {
    if (!data.length) {
      return <div className="flex items-center justify-center h-full text-gray-500">Loading data...</div>;
    }

    if (viewMode === 'raw') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey="sessionLength" 
              type="number" 
              domain={['dataMin - 1', 'dataMax + 1']}
              label={{ value: 'Session Length (seconds)', position: 'insideBottom', offset: -10 }}
            />
            <YAxis 
              domain={[0, 100]}
              label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Success Rate']}
              labelFormatter={(value: any) => `Session Length: ${Number(value).toFixed(1)}s`}
            />
            <Scatter dataKey="successRate" fill="#4F46E5" fillOpacity={0.7} />
          </ScatterChart>
        </ResponsiveContainer>
      );
    } else {
      const smoothedData = getSmoothedData();
      return (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={smoothedData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey="sessionLength"
              type="number"
              domain={['dataMin - 1', 'dataMax + 1']}
              label={{ value: 'Session Length (seconds)', position: 'insideBottom', offset: -10 }}
            />
            <YAxis 
              domain={[0, 100]}
              label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Success Rate']}
              labelFormatter={(value: any) => `Session Length: ${Number(value).toFixed(1)}s`}
            />
            <Line 
              dataKey="successRate" 
              stroke="#DC2626" 
              strokeWidth={3}
              dot={{ fill: '#DC2626', r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Session Performance Analyzer</h1>
          <p className="text-gray-600 mb-4">Analytics for session length vs success rate correlation</p>
          
          {/* Data Source Info */}
          <div className="flex items-center gap-2 text-sm">
            <span className="font-medium">Data source:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              isUsingCustomData 
                ? 'bg-green-100 text-green-800' 
                : 'bg-blue-100 text-blue-800'
            }`}>
              {isUsingCustomData ? '📁 Custom CSV Data' : '🧪 Sample Data'}
            </span>
            <span className="text-gray-500">({stats.totalSessions} sessions)</span>
          </div>
        </div>

        {/* Data Management */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📊 Data Management</h2>
          <div className="flex flex-col md:flex-row gap-4">
            
            {/* File Upload Section */}
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Upload Your Data</h3>
              <div className="flex items-center gap-3">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept=".csv"
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadStatus === 'uploading'}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                    uploadStatus === 'uploading'
                      ? 'bg-gray-400 text-white cursor-not-allowed'
                      : uploadStatus === 'success'
                      ? 'bg-green-600 hover:bg-green-700 text-white'
                      : uploadStatus === 'error'
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  <Upload className="w-4 h-4" />
                  {uploadStatus === 'uploading' ? 'Uploading...' :
                   uploadStatus === 'success' ? 'Upload New File' :
                   uploadStatus === 'error' ? 'Try Again' : 'Upload CSV File'}
                </button>
                <div className="text-xs text-gray-500 flex items-center gap-2">
                  <span>Expected format: session_number, session_length, success_rate</span>
                  <a 
                    href="/session-performance-analyzer/sample_data.csv" 
                    download="sample_data.csv"
                    className="text-blue-600 hover:text-blue-800 underline"
                  >
                    📥 Download Sample
                  </a>
                </div>
              </div>
            </div>

            {/* Sample Data Section */}
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Use Sample Data</h3>
              <div className="flex items-center gap-3">
                <button
                  onClick={loadSampleData}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
                >
                  <BarChart3 className="w-4 h-4" />
                  Load Demo Data
                </button>
                <span className="text-xs text-gray-500">
                  200 sessions with realistic performance curve
                </span>
              </div>
            </div>

            {/* Export Section */}
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Export Results</h3>
              <div className="flex items-center gap-3">
                <button
                  onClick={exportData}
                  disabled={data.length === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Export CSV
                </button>
                <span className="text-xs text-gray-500">
                  Download current dataset
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Analysis Controls */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🔧 Analysis Controls</h2>
          <div className="flex flex-col md:flex-row gap-6 items-center">
            <div className="flex items-center gap-2">
              <label className="font-medium text-gray-700">View Mode:</label>
              <select 
                value={viewMode} 
                onChange={(e) => setViewMode(e.target.value as 'raw' | 'trend')}
                className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
              >
                <option value="raw">Raw Data Points</option>
                <option value="trend">Smoothed Trend</option>
              </select>
            </div>
            
            {viewMode === 'trend' && (
              <div className="flex items-center gap-2">
                <label className="font-medium text-gray-700">Smoothing Level:</label>
                <input
                  type="range"
                  min="5"
                  max="25"
                  value={smoothingLevel}
                  onChange={(e) => setSmoothingLevel(parseInt(e.target.value))}
                  className="w-32"
                />
                <span className="text-sm text-gray-600 w-8 font-mono">{smoothingLevel}</span>
                <span className="text-xs text-gray-500">sessions</span>
              </div>
            )}
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard 
            title="Total Sessions" 
            value={stats.totalSessions} 
            icon={BarChart3} 
            color="border-blue-500" 
          />
          <StatCard 
            title="Inflection Point" 
            value={`${stats.inflectionPoint}s`} 
            icon={TrendingDown} 
            color="border-orange-500" 
          />
          <StatCard 
            title="Early Success Rate" 
            value={`${stats.earlySuccessRate}%`} 
            icon={BarChart3} 
            color="border-green-500" 
          />
          <StatCard 
            title="Late Success Rate" 
            value={`${stats.lateSuccessRate}%`} 
            icon={AlertTriangle} 
            color="border-red-500" 
          />
        </div>

        {/* Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Success Rate vs Session Length</h2>
          <div className="h-96">
            {renderChart()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SessionAnalyzer;
