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
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
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

    const sampleData = generateSampleData();
    setData(sampleData);
    
    const earlyData = sampleData.slice(0, 130);
    const lateData = sampleData.slice(130);
    const inflectionPoint = 1.0 + (130 - 1) * 0.2;
    
    setStats({
      totalSessions: sampleData.length,
      inflectionPoint: inflectionPoint.toFixed(1),
      earlySuccessRate: (earlyData.reduce((sum, p) => sum + p.successRate, 0) / earlyData.length).toFixed(1),
      lateSuccessRate: (lateData.reduce((sum, p) => sum + p.successRate, 0) / lateData.length).toFixed(1),
    });
  }, []);

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

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const _csvText = e.target?.result as string;
          console.log('File uploaded:', file.name);
          alert(`File "${file.name}" uploaded successfully! CSV parsing will be implemented in a future version.`);
        } catch (error) {
          console.error('Error parsing file:', error);
          alert('Error parsing file. Please check the format.');
        }
      };
      reader.readAsText(file);
    }
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
          <p className="text-gray-600">Analytics for session length vs success rate correlation</p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4 items-center">
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
            
            <div className="flex items-center gap-2">
              <label className="font-medium text-gray-700">Smoothing Level:</label>
              <input
                type="range"
                min="5"
                max="25"
                value={smoothingLevel}
                onChange={(e) => setSmoothingLevel(parseInt(e.target.value))}
                className="w-24"
              />
              <span className="text-sm text-gray-600 w-8">{smoothingLevel}</span>
            </div>

            {/* Upload and Export Buttons */}
            <div className="flex gap-2 ml-auto">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".csv"
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Upload className="w-4 h-4" />
                Upload Data
              </button>
              <button
                onClick={exportData}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
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
