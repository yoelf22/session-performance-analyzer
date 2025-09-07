import React, { useState, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { BarChart3, TrendingDown, AlertTriangle, Upload, Download } from 'lucide-react';

interface ShopifyData {
  sessionId: string;
  orderId?: string;
  successRate: number;
  timestamp?: string;
}

interface AWSData {
  sessionId: string;
  sessionLength: number;
  userId?: string;
  timestamp?: string;
}

interface FusedDataPoint {
  sessionId: string;
  sessionLength: number;
  successRate: number;
  sessionNumber: number; // For chart compatibility
}

const SessionAnalyzer: React.FC = () => {
  // Generate initial sample data immediately  
  const generateSampleDataImmediate = (): FusedDataPoint[] => {
    const points: FusedDataPoint[] = [];
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
        sessionId: `session_${i}`,
        sessionNumber: i,
        sessionLength: Number(sessionLength.toFixed(2)),
        successRate: Number((successRate * 100).toFixed(2)),
      });
    }
    return points;
  };

  const initialSampleData = generateSampleDataImmediate();
  const [fusedData, setFusedData] = useState<FusedDataPoint[]>(initialSampleData);
  const [shopifyData, setShopifyData] = useState<ShopifyData[]>([]);
  const [awsData, setAWSData] = useState<AWSData[]>([]);
  const [viewMode, setViewMode] = useState<'raw' | 'trend'>('raw');
  const [smoothingLevel, setSmoothingLevel] = useState<number>(10);
  const [stats, setStats] = useState({
    totalSessions: initialSampleData.length,
    matchedSessions: initialSampleData.length,
    inflectionPoint: '27.0',
    earlySuccessRate: '80.5',
    lateSuccessRate: '5.0',
  });
  const [shopifyUploadStatus, setShopifyUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [awsUploadStatus, setAWSUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [isReportGenerated, setIsReportGenerated] = useState(true);
  const shopifyFileRef = useRef<HTMLInputElement>(null);
  const awsFileRef = useRef<HTMLInputElement>(null);

  const generateSampleData = (): FusedDataPoint[] => {
    const points: FusedDataPoint[] = [];
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
        sessionId: `session_${i}`,
        sessionNumber: i,
        sessionLength: Number(sessionLength.toFixed(2)),
        successRate: Number((successRate * 100).toFixed(2)),
      });
    }
    return points;
  };

  const getSmoothedData = (): FusedDataPoint[] => {
    if (!fusedData.length) return [];
    
    const smoothed: FusedDataPoint[] = [];
    for (let i = 0; i < fusedData.length; i += smoothingLevel) {
      const chunk = fusedData.slice(i, i + smoothingLevel);
      if (chunk.length === 0) continue;
      
      const avgLength = chunk.reduce((sum, p) => sum + p.sessionLength, 0) / chunk.length;
      const avgSuccess = chunk.reduce((sum, p) => sum + p.successRate, 0) / chunk.length;
      
      smoothed.push({
        sessionId: `smoothed_${i}`,
        sessionNumber: Math.round(i + smoothingLevel / 2),
        sessionLength: Number(avgLength.toFixed(2)),
        successRate: Number(avgSuccess.toFixed(2)),
      });
    }
    return smoothed;
  };

  const parseShopifyCSV = (csvText: string): ShopifyData[] => {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('Shopify CSV must have at least a header row and one data row');
    }
    
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const data: ShopifyData[] = [];
    
    // Find column indices for Shopify data
    const sessionIdIndex = headers.findIndex(h => 
      h.includes('session') && (h.includes('id') || h.includes('identifier'))
    );
    const orderIdIndex = headers.findIndex(h => 
      h.includes('order') && h.includes('id')
    );
    const successRateIndex = headers.findIndex(h => 
      h.includes('success') && (h.includes('rate') || h.includes('percent') || h.includes('%'))
    );
    const timestampIndex = headers.findIndex(h => 
      h.includes('timestamp') || h.includes('date') || h.includes('time')
    );
    
    if (sessionIdIndex === -1 || successRateIndex === -1) {
      throw new Error('Shopify CSV must contain columns for session_id and success_rate');
    }
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
      if (values.length < 2) continue;
      
      const sessionId = values[sessionIdIndex];
      const successRateStr = values[successRateIndex];
      const successRate = parseFloat(successRateStr);
      
      if (sessionId && !isNaN(successRate)) {
        data.push({
          sessionId,
          orderId: orderIdIndex >= 0 ? values[orderIdIndex] : undefined,
          successRate: successRate > 1 ? successRate : successRate * 100,
          timestamp: timestampIndex >= 0 ? values[timestampIndex] : undefined,
        });
      }
    }
    
    if (data.length === 0) {
      throw new Error('No valid Shopify data rows found in CSV');
    }
    
    return data;
  };

  const parseAWSCSV = (csvText: string): AWSData[] => {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('AWS CSV must have at least a header row and one data row');
    }
    
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const data: AWSData[] = [];
    
    // Find column indices for AWS data
    const sessionIdIndex = headers.findIndex(h => 
      h.includes('session') && (h.includes('id') || h.includes('identifier'))
    );
    const sessionLengthIndex = headers.findIndex(h => 
      h.includes('session') && (h.includes('length') || h.includes('duration') || h.includes('time'))
    );
    const userIdIndex = headers.findIndex(h => 
      h.includes('user') && h.includes('id')
    );
    const timestampIndex = headers.findIndex(h => 
      h.includes('timestamp') || h.includes('date') || h.includes('time')
    );
    
    if (sessionIdIndex === -1 || sessionLengthIndex === -1) {
      throw new Error('AWS CSV must contain columns for session_id and session_length');
    }
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
      if (values.length < 2) continue;
      
      const sessionId = values[sessionIdIndex];
      const sessionLength = parseFloat(values[sessionLengthIndex]);
      
      if (sessionId && !isNaN(sessionLength)) {
        data.push({
          sessionId,
          sessionLength,
          userId: userIdIndex >= 0 ? values[userIdIndex] : undefined,
          timestamp: timestampIndex >= 0 ? values[timestampIndex] : undefined,
        });
      }
    }
    
    if (data.length === 0) {
      throw new Error('No valid AWS data rows found in CSV');
    }
    
    return data;
  };

  const fuseData = (): FusedDataPoint[] => {
    if (shopifyData.length === 0 || awsData.length === 0) {
      return [];
    }
    
    const fused: FusedDataPoint[] = [];
    let sessionCounter = 1;
    
    // Create lookup map for AWS data by session ID
    const awsMap = new Map<string, AWSData>();
    awsData.forEach(aws => awsMap.set(aws.sessionId, aws));
    
    // Match Shopify data with AWS data by session ID
    shopifyData.forEach(shopify => {
      const awsMatch = awsMap.get(shopify.sessionId);
      if (awsMatch) {
        fused.push({
          sessionId: shopify.sessionId,
          sessionLength: awsMatch.sessionLength,
          successRate: shopify.successRate,
          sessionNumber: sessionCounter++
        });
      }
    });
    
    // Sort by session length for better visualization
    return fused.sort((a, b) => a.sessionLength - b.sessionLength);
  };

  const generateFusionReport = () => {
    if (shopifyData.length === 0 || awsData.length === 0) {
      alert('Both Shopify and AWS data must be uploaded before generating a fusion report.');
      return;
    }

    const fused = fuseData();
    
    if (fused.length === 0) {
      alert(`No matching sessions found between Shopify data (${shopifyData.length} sessions) and AWS data (${awsData.length} sessions). Please ensure both datasets contain matching session_id values.`);
      return;
    }
    
    const totalSessions = Math.max(shopifyData.length, awsData.length);
    const matchedSessions = fused.length;
    const matchRate = ((matchedSessions / totalSessions) * 100).toFixed(1);
    
    setFusedData(fused);
    
    // Calculate statistics
    const earlyData = fused.slice(0, Math.floor(fused.length * 0.65));
    const lateData = fused.slice(Math.floor(fused.length * 0.65));
    const inflectionPoint = fused.length > 0 ? fused[Math.floor(fused.length * 0.65)]?.sessionLength || 0 : 0;
    
    setStats({
      totalSessions: totalSessions,
      matchedSessions: matchedSessions,
      inflectionPoint: inflectionPoint.toFixed(1),
      earlySuccessRate: earlyData.length > 0 ? (earlyData.reduce((sum, p) => sum + p.successRate, 0) / earlyData.length).toFixed(1) : '0',
      lateSuccessRate: lateData.length > 0 ? (lateData.reduce((sum, p) => sum + p.successRate, 0) / lateData.length).toFixed(1) : '0',
    });
    
    setIsReportGenerated(true);
    alert(`Fusion report generated! Matched ${matchedSessions} sessions out of ${totalSessions} total (${matchRate}% match rate).`);
  };

  const handleShopifyUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setShopifyUploadStatus('error');
      alert('Please upload a CSV file');
      return;
    }
    
    setShopifyUploadStatus('uploading');
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const csvText = String(e.target?.result ?? '');
        const parsedData = parseShopifyCSV(csvText);
        
        setShopifyData(parsedData);
        setShopifyUploadStatus('success');
        setIsReportGenerated(false); // Reset report when new data is uploaded
        
        alert(`Successfully loaded ${parsedData.length} Shopify records from ${file.name}`);
      } catch (error) {
        console.error('Error parsing Shopify CSV:', error);
        setShopifyUploadStatus('error');
        alert(`Error parsing Shopify CSV: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    };
    
    reader.onerror = () => {
      setShopifyUploadStatus('error');
      alert('Error reading Shopify file');
    };
    
    reader.readAsText(file);
    
    // Reset file input
    if (event.target) event.target.value = '';
  };

  const handleAWSUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setAWSUploadStatus('error');
      alert('Please upload a CSV file');
      return;
    }
    
    setAWSUploadStatus('uploading');
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const csvText = String(e.target?.result ?? '');
        const parsedData = parseAWSCSV(csvText);
        
        setAWSData(parsedData);
        setAWSUploadStatus('success');
        setIsReportGenerated(false); // Reset report when new data is uploaded
        
        alert(`Successfully loaded ${parsedData.length} AWS session records from ${file.name}`);
      } catch (error) {
        console.error('Error parsing AWS CSV:', error);
        setAWSUploadStatus('error');
        alert(`Error parsing AWS CSV: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    };
    
    reader.onerror = () => {
      setAWSUploadStatus('error');
      alert('Error reading AWS file');
    };
    
    reader.readAsText(file);
    
    // Reset file input
    if (event.target) event.target.value = '';
  };

  const loadSampleData = () => {
    const sampleData = generateSampleData();
    setFusedData(sampleData);
    setShopifyUploadStatus('idle');
    setAWSUploadStatus('idle');
    setIsReportGenerated(true);
    
    const earlyData = sampleData.slice(0, 130);
    const lateData = sampleData.slice(130);
    const inflectionPoint = 1.0 + (130 - 1) * 0.2;
    
    setStats({
      totalSessions: sampleData.length,
      matchedSessions: sampleData.length,
      inflectionPoint: inflectionPoint.toFixed(1),
      earlySuccessRate: (earlyData.reduce((sum, p) => sum + p.successRate, 0) / earlyData.length).toFixed(1),
      lateSuccessRate: (lateData.reduce((sum, p) => sum + p.successRate, 0) / lateData.length).toFixed(1),
    });
  };

  const exportData = () => {
    const csvContent = [
      'Session ID,Session Number,Session Length,Success Rate',
      ...fusedData.map(row => `${row.sessionId},${row.sessionNumber},${row.sessionLength},${row.successRate}`)
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'session_fusion_analysis_results.csv';
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
    if (!fusedData.length) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          No fused data available. Please upload both Shopify and AWS data files or click "Load Demo Data".
        </div>
      );
    }

    // Create chart data with proper structure
    const chartData = fusedData.map(point => ({
      sessionLength: point.sessionLength,
      successRate: point.successRate,
      sessionId: point.sessionId
    }));

    if (viewMode === 'raw') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart 
            data={chartData} 
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey="sessionLength"
              type="number" 
              domain={['dataMin - 1', 'dataMax + 1']}
              label={{ 
                value: 'Session Length (seconds)', 
                position: 'insideBottom', 
                offset: -10 
              }}
            />
            <YAxis 
              domain={[0, 100]}
              label={{ 
                value: 'Success Rate (%)', 
                angle: -90, 
                position: 'insideLeft' 
              }}
            />
            <Tooltip 
              formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Success Rate']}
              labelFormatter={(value: any) => `Session Length: ${Number(value).toFixed(1)}s`}
            />
            <Scatter 
              dataKey="successRate" 
              fill="#4F46E5" 
              fillOpacity={0.7} 
            />
          </ScatterChart>
        </ResponsiveContainer>
      );
    } else {
      const smoothedData = getSmoothedData().map(point => ({
        sessionLength: point.sessionLength,
        successRate: point.successRate
      }));
      
      return (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart 
            data={smoothedData} 
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey="sessionLength"
              type="number"
              domain={['dataMin - 1', 'dataMax + 1']}
              label={{ 
                value: 'Session Length (seconds)', 
                position: 'insideBottom', 
                offset: -10 
              }}
            />
            <YAxis 
              domain={[0, 100]}
              label={{ 
                value: 'Success Rate (%)', 
                angle: -90, 
                position: 'insideLeft' 
              }}
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
          
          {/* Debug status */}
          <div className="bg-green-100 border border-green-300 rounded p-2 mb-4">
            <span className="text-green-800 text-sm font-medium">✅ React App Loaded Successfully - Chart Data: {fusedData.length} points</span>
          </div>
          
          {/* Data Source Info */}
          <div className="flex items-center gap-2 text-sm">
            <span className="font-medium">Data source:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              isReportGenerated 
                ? 'bg-green-100 text-green-800' 
                : 'bg-blue-100 text-blue-800'
            }`}>
              {isReportGenerated ? '🔗 Fused Data Report' : '⏳ Awaiting Data Fusion'}
            </span>
            <span className="text-gray-500">({stats.totalSessions} sessions, {stats.matchedSessions} matched)</span>
          </div>
        </div>

        {/* Data Management */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📊 Data Management</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Shopify Data Section */}
            <div className="border-2 border-dashed border-orange-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg">🛒</span>
                <h3 className="text-base font-medium text-gray-900">Shopify Data (Success Metrics)</h3>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                  shopifyUploadStatus === 'success' 
                    ? 'bg-green-100 text-green-800' 
                    : shopifyUploadStatus === 'error'
                    ? 'bg-red-100 text-red-800'
                    : shopifyUploadStatus === 'uploading'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {shopifyUploadStatus === 'success' ? '✓ Loaded' :
                   shopifyUploadStatus === 'error' ? '✗ Error' :
                   shopifyUploadStatus === 'uploading' ? '↻ Loading' : 'Pending'}
                </div>
              </div>
              
              <input
                type="file"
                ref={shopifyFileRef}
                onChange={handleShopifyUpload}
                accept=".csv"
                className="hidden"
              />
              
              <button
                onClick={() => shopifyFileRef.current?.click()}
                disabled={shopifyUploadStatus === 'uploading'}
                className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors mb-3 ${
                  shopifyUploadStatus === 'uploading'
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : shopifyUploadStatus === 'success'
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : shopifyUploadStatus === 'error'
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-orange-600 hover:bg-orange-700 text-white'
                }`}
              >
                <Upload className="w-4 h-4" />
                {shopifyUploadStatus === 'uploading' ? 'Uploading Shopify Data...' :
                 shopifyUploadStatus === 'success' ? `Replace Shopify File (${shopifyData.length} records)` :
                 shopifyUploadStatus === 'error' ? 'Try Again' : 'Upload Shopify CSV'}
              </button>
              
              <div className="text-xs text-gray-600">
                Required columns: <code>session_id</code>, <code>success_rate</code><br/>
                Optional: <code>order_id</code>, <code>timestamp</code><br/>
                <a 
                  href="/session-performance-analyzer/shopify_sample.csv" 
                  download="shopify_sample.csv"
                  className="text-orange-600 hover:text-orange-800 underline"
                >
                  📥 Download Shopify Sample
                </a>
              </div>
            </div>

            {/* AWS Data Section */}
            <div className="border-2 border-dashed border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg">☁️</span>
                <h3 className="text-base font-medium text-gray-900">AWS Data (Session Lengths)</h3>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                  awsUploadStatus === 'success' 
                    ? 'bg-green-100 text-green-800' 
                    : awsUploadStatus === 'error'
                    ? 'bg-red-100 text-red-800'
                    : awsUploadStatus === 'uploading'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {awsUploadStatus === 'success' ? '✓ Loaded' :
                   awsUploadStatus === 'error' ? '✗ Error' :
                   awsUploadStatus === 'uploading' ? '↻ Loading' : 'Pending'}
                </div>
              </div>
              
              <input
                type="file"
                ref={awsFileRef}
                onChange={handleAWSUpload}
                accept=".csv"
                className="hidden"
              />
              
              <button
                onClick={() => awsFileRef.current?.click()}
                disabled={awsUploadStatus === 'uploading'}
                className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors mb-3 ${
                  awsUploadStatus === 'uploading'
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : awsUploadStatus === 'success'
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : awsUploadStatus === 'error'
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                <Upload className="w-4 h-4" />
                {awsUploadStatus === 'uploading' ? 'Uploading AWS Data...' :
                 awsUploadStatus === 'success' ? `Replace AWS File (${awsData.length} records)` :
                 awsUploadStatus === 'error' ? 'Try Again' : 'Upload AWS CSV'}
              </button>
              
              <div className="text-xs text-gray-600">
                Required columns: <code>session_id</code>, <code>session_length</code><br/>
                Optional: <code>user_id</code>, <code>timestamp</code><br/>
                <a 
                  href="/session-performance-analyzer/aws_sample.csv" 
                  download="aws_sample.csv"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  📥 Download AWS Sample
                </a>
              </div>
            </div>
          </div>

          {/* Action Buttons Row */}
          <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-gray-200">
            {/* Generate Fusion Report Button */}
            <div className="flex-1">
              <button
                onClick={generateFusionReport}
                disabled={shopifyUploadStatus !== 'success' || awsUploadStatus !== 'success'}
                className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                  shopifyUploadStatus === 'success' && awsUploadStatus === 'success'
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                <span className="text-base">🔗</span>
                Generate Fusion Report
              </button>
              {shopifyUploadStatus !== 'success' || awsUploadStatus !== 'success' ? (
                <p className="text-xs text-gray-500 text-center mt-1">
                  Upload both data sources to enable fusion
                </p>
              ) : (
                <p className="text-xs text-green-600 text-center mt-1">
                  Ready to generate fusion report
                </p>
              )}
            </div>

            {/* Sample Data Button */}
            <div className="flex-1">
              <button
                onClick={loadSampleData}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
              >
                <BarChart3 className="w-4 h-4" />
                Load Demo Data
              </button>
              <p className="text-xs text-gray-500 text-center mt-1">
                200 sessions with realistic performance curve
              </p>
            </div>

            {/* Export Button */}
            <div className="flex-1">
              <button
                onClick={exportData}
                disabled={fusedData.length === 0}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                <Download className="w-4 h-4" />
                Export Results
              </button>
              <p className="text-xs text-gray-500 text-center mt-1">
                Download fused dataset
              </p>
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatCard 
            title="Total Sessions" 
            value={stats.totalSessions} 
            icon={BarChart3} 
            color="border-blue-500" 
          />
          <StatCard 
            title="Matched Sessions" 
            value={stats.matchedSessions} 
            icon={BarChart3} 
            color="border-purple-500" 
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
