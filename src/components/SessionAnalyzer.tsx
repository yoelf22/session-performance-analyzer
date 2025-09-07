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
  // Start with empty data - user must upload files to begin session
  const [fusedData, setFusedData] = useState<FusedDataPoint[]>([]);
  const [shopifyData, setShopifyData] = useState<ShopifyData[]>([]);
  const [awsData, setAWSData] = useState<AWSData[]>([]);
  const [viewMode, setViewMode] = useState<'raw' | 'trend'>('raw');
  const [smoothingLevel, setSmoothingLevel] = useState<number>(10);
  const [stats, setStats] = useState({
    totalSessions: 0,
    matchedSessions: 0,
    inflectionPoint: '0',
    earlySuccessRate: '0',
    lateSuccessRate: '0',
  });
  const [shopifyUploadStatus, setShopifyUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [awsUploadStatus, setAWSUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [isReportGenerated, setIsReportGenerated] = useState(false);
  const [shopifyMessage, setShopifyMessage] = useState<string>('');
  const [awsMessage, setAWSMessage] = useState<string>('');
  const [fusionMessage, setFusionMessage] = useState<string>('');
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
    
    // Find column indices for Shopify data - robust matching
    const sessionIdIndex = headers.findIndex(h => 
      h === 'session_id' || h === 'sessionid' || h === 'session-id' || 
      (h.includes('session') && h.includes('id'))
    );
    const orderIdIndex = headers.findIndex(h => 
      h === 'order_id' || h === 'orderid' || h === 'order-id' ||
      (h.includes('order') && h.includes('id'))
    );
    const successRateIndex = headers.findIndex(h => 
      h === 'success_rate' || h === 'successrate' || h === 'success-rate' ||
      h === 'success_percent' || h === 'success_percentage' || h === 'success' ||
      (h.includes('success') && (h.includes('rate') || h.includes('percent'))) ||
      h.includes('success')
    );
    const timestampIndex = headers.findIndex(h => 
      h.includes('timestamp') || h.includes('date') || h.includes('time')
    );
    
    if (sessionIdIndex === -1 || successRateIndex === -1) {
      const missingColumns = [];
      if (sessionIdIndex === -1) missingColumns.push('session_id');
      if (successRateIndex === -1) missingColumns.push('success or success_rate');
      throw new Error(`Missing required columns: ${missingColumns.join(', ')}. Found headers: ${headers.join(', ')}`);
    }
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
      if (values.length < 2) continue;
      
      const sessionId = values[sessionIdIndex];
      const successRateStr = values[successRateIndex];
      const successRate = parseFloat(successRateStr);
      
      if (sessionId && !isNaN(successRate)) {
        // Convert success rate to percentage (0-100 range)
        let normalizedSuccessRate = successRate;
        if (successRate <= 1) {
          // Assume it's a decimal (0.45 -> 45%)
          normalizedSuccessRate = successRate * 100;
        }
        // If > 1, assume it's already a percentage
        
        data.push({
          sessionId,
          orderId: orderIdIndex >= 0 ? values[orderIdIndex] : undefined,
          successRate: Number(normalizedSuccessRate.toFixed(2)),
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
    
    // Show complete diagnostic info
    console.log('=== AWS CSV DIAGNOSTIC ===');
    console.log('Total lines:', lines.length);
    console.log('Headers found:', headers);
    console.log('First 3 data lines:');
    lines.slice(1, 4).forEach((line, index) => {
      console.log(`Line ${index + 2}: "${line}"`);
      const values = line.split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
      console.log(`  Split values: [${values.map(v => `"${v}"`).join(', ')}]`);
    });
    
    // Find column indices for AWS data - very flexible matching
    const sessionIdIndex = headers.findIndex(h => 
      h === 'session_id' || h === 'sessionid' || h === 'session-id' || 
      (h.includes('session') && h.includes('id')) ||
      h === 'session' || h === 'id'
    );
    // Look for direct session length column first
    let sessionLengthIndex = headers.findIndex(h => 
      h === 'session_length' || h === 'sessionlength' || h === 'session-length' ||
      h === 'session_duration' || h === 'duration' || h === 'length' ||
      (h.includes('session') && (h.includes('length') || h.includes('duration'))) ||
      (h.includes('duration')) || (h.includes('length'))
    );
    
    // If no direct session length, look for start/end timestamp columns - be more flexible
    let startTimestampIndex = -1;
    let endTimestampIndex = -1;
    
    if (sessionLengthIndex === -1) {
      startTimestampIndex = headers.findIndex(h => 
        h.includes('start') && (h.includes('timestamp') || h.includes('time')) ||
        h === 'start_timestamp' || h === 'starttime' || h === 'start_time' ||
        h === 'start' || h === 'begin_timestamp' || h === 'begin_time'
      );
      endTimestampIndex = headers.findIndex(h => 
        h.includes('end') && (h.includes('timestamp') || h.includes('time')) ||
        h === 'end_timestamp' || h === 'endtime' || h === 'end_time' ||
        h === 'end' || h === 'finish_timestamp' || h === 'finish_time'
      );
    }
    const userIdIndex = headers.findIndex(h => 
      h === 'user_id' || h === 'userid' || h === 'user-id' ||
      (h.includes('user') && h.includes('id')) || h === 'user'
    );
    const timestampIndex = headers.findIndex(h => 
      h.includes('timestamp') || h.includes('date') || h.includes('time')
    );
    
    console.log('Column matching results:', {
      sessionIdIndex,
      sessionLengthIndex,
      startTimestampIndex,
      endTimestampIndex,
      userIdIndex,
      timestampIndex
    });
    
    if (sessionIdIndex === -1 || (sessionLengthIndex === -1 && (startTimestampIndex === -1 || endTimestampIndex === -1))) {
      const missingColumns = [];
      if (sessionIdIndex === -1) missingColumns.push('session_id (or similar)');
      if (sessionLengthIndex === -1 && (startTimestampIndex === -1 || endTimestampIndex === -1)) {
        missingColumns.push('session_length OR (start_timestamp AND end_timestamp)');
      }
      
      console.error('Column detection failed. Available headers:', headers);
      console.error('Looking for session ID in columns containing: session_id, sessionid, session-id, session, id');
      console.error('Looking for timestamps in columns containing: start_timestamp, end_timestamp, starttime, endtime, etc.');
      
      throw new Error(`❌ Cannot find required columns. Looking for: ${missingColumns.join(' AND ')}. Available columns: ${headers.join(', ')}`);
    }
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
      if (values.length < 2) continue;
      
      const sessionId = values[sessionIdIndex];
      let sessionLength: number;
      
      if (sessionLengthIndex >= 0) {
        // Direct session length column
        sessionLength = parseFloat(values[sessionLengthIndex]);
      } else {
        // Calculate from start/end timestamps
        const startTime = values[startTimestampIndex];
        const endTime = values[endTimestampIndex];
        
        try {
          let startMs: number;
          let endMs: number;
          
          // Check if timestamps are Unix timestamps (numbers) or date strings
          const startNum = parseFloat(startTime);
          const endNum = parseFloat(endTime);
          
          if (!isNaN(startNum) && !isNaN(endNum) && startTime.match(/^\d+\.?\d*$/) && endTime.match(/^\d+\.?\d*$/)) {
            // Unix timestamps (seconds since epoch)
            console.log(`Unix timestamps detected: start=${startNum}, end=${endNum}`);
            
            // Convert from seconds to milliseconds
            if (startNum < 1e10) {
              // Seconds since epoch (typical Unix timestamp)
              startMs = startNum * 1000;
              endMs = endNum * 1000;
            } else {
              // Already in milliseconds
              startMs = startNum;
              endMs = endNum;
            }
          } else {
            // ISO date strings - handle both formats: "2024-01-01 10:00:00" and "2024-01-01T10:00:00Z"
            console.log(`ISO timestamps detected: start="${startTime}", end="${endTime}"`);
            const normalizedStartTime = startTime.includes('T') ? startTime : startTime.replace(' ', 'T');
            const normalizedEndTime = endTime.includes('T') ? endTime : endTime.replace(' ', 'T');
            
            const start = new Date(normalizedStartTime);
            const end = new Date(normalizedEndTime);
            
            if (isNaN(start.getTime()) || isNaN(end.getTime())) {
              throw new Error('Invalid ISO timestamp format');
            }
            
            startMs = start.getTime();
            endMs = end.getTime();
          }
          
          if (isNaN(startMs) || isNaN(endMs)) {
            throw new Error('Invalid timestamp values');
          }
          
          sessionLength = (endMs - startMs) / 1000; // Convert to seconds
          console.log(`Session ${sessionId}: ${sessionLength} seconds (${startMs} -> ${endMs})`);
        } catch (error) {
          console.warn(`Failed to parse timestamps for session ${sessionId}: start="${startTime}", end="${endTime}"`, error);
          continue; // Skip this row if timestamp parsing fails
        }
      }
      
      if (sessionId && !isNaN(sessionLength) && sessionLength > 0) {
        data.push({
          sessionId,
          sessionLength: Number(sessionLength.toFixed(2)),
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
    
    console.log('=== DATA FUSION DEBUG ===');
    console.log(`Shopify data: ${shopifyData.length} records`);
    console.log(`AWS data: ${awsData.length} records`);
    
    // Show sample session IDs from both datasets
    console.log('Sample Shopify session IDs:', shopifyData.slice(0, 5).map(s => s.sessionId));
    console.log('Sample AWS session IDs:', awsData.slice(0, 5).map(a => a.sessionId));
    
    const fused: FusedDataPoint[] = [];
    let sessionCounter = 1;
    
    // Create lookup map for AWS data by session ID
    const awsMap = new Map<string, AWSData>();
    awsData.forEach(aws => awsMap.set(aws.sessionId, aws));
    
    console.log('AWS session IDs available:', Array.from(awsMap.keys()).slice(0, 10));
    
    let matchCount = 0;
    let sampleMatches: string[] = [];
    let sampleMismatches: string[] = [];
    
    // Match Shopify data with AWS data by session ID
    shopifyData.forEach(shopify => {
      const awsMatch = awsMap.get(shopify.sessionId);
      if (awsMatch) {
        matchCount++;
        if (sampleMatches.length < 5) {
          sampleMatches.push(shopify.sessionId);
        }
        fused.push({
          sessionId: shopify.sessionId,
          sessionLength: awsMatch.sessionLength,
          successRate: shopify.successRate,
          sessionNumber: sessionCounter++
        });
      } else {
        if (sampleMismatches.length < 5) {
          sampleMismatches.push(shopify.sessionId);
        }
      }
    });
    
    console.log(`Fusion results: ${matchCount} matches out of ${shopifyData.length} Shopify records`);
    console.log('Sample matching session IDs:', sampleMatches);
    console.log('Sample non-matching Shopify session IDs:', sampleMismatches);
    
    if (fused.length === 0) {
      console.error('❌ NO MATCHES FOUND!');
      console.error('This usually means session IDs between files don\'t match exactly.');
      console.error('Check for differences in format, prefixes, or case sensitivity.');
    }
    
    // Sort by session length for better visualization
    return fused.sort((a, b) => a.sessionLength - b.sessionLength);
  };

  const generateFusionReport = () => {
    if (shopifyData.length === 0 || awsData.length === 0) {
      setFusionMessage('Both Shopify and AWS data must be uploaded before generating a fusion report.');
      return;
    }

    const fused = fuseData();
    
    if (fused.length === 0) {
      setFusionMessage(`No matching sessions found between Shopify data (${shopifyData.length} sessions) and AWS data (${awsData.length} sessions). Please ensure both datasets contain matching session_id values.`);
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
    setFusionMessage(`✅ Fusion report generated! Matched ${matchedSessions} sessions out of ${totalSessions} total (${matchRate}% match rate).`);
  };

  const handleShopifyUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setShopifyUploadStatus('error');
      setShopifyMessage('Please upload a CSV file');
      return;
    }
    
    // Clear all previous session data when starting new upload
    setFusedData([]);
    setIsReportGenerated(false);
    setFusionMessage('');
    setStats({
      totalSessions: 0,
      matchedSessions: 0,
      inflectionPoint: '0',
      earlySuccessRate: '0',
      lateSuccessRate: '0',
    });
    
    setShopifyUploadStatus('uploading');
    setShopifyMessage('');
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const csvText = String(e.target?.result ?? '');
      try {
        const parsedData = parseShopifyCSV(csvText);
        
        setShopifyData(parsedData);
        setShopifyUploadStatus('success');
        setShopifyMessage(`✅ Successfully loaded ${parsedData.length} records`);
      } catch (error) {
        console.error('Error parsing Shopify CSV:', error);
        setShopifyUploadStatus('error');
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setShopifyMessage(`❌ ${errorMessage}`);
      }
    };
    
    reader.onerror = () => {
      setShopifyUploadStatus('error');
      setShopifyMessage('❌ Error reading file');
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
      setAWSMessage('Please upload a CSV file');
      return;
    }
    
    // Clear all previous session data when starting new upload
    setFusedData([]);
    setIsReportGenerated(false);
    setFusionMessage('');
    setStats({
      totalSessions: 0,
      matchedSessions: 0,
      inflectionPoint: '0',
      earlySuccessRate: '0',
      lateSuccessRate: '0',
    });
    
    setAWSUploadStatus('uploading');
    setAWSMessage('');
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const csvText = String(e.target?.result ?? '');
      try {
        const parsedData = parseAWSCSV(csvText);
        
        setAWSData(parsedData);
        setAWSUploadStatus('success');
        setAWSMessage(`✅ Successfully loaded ${parsedData.length} records`);
      } catch (error) {
        console.error('Error parsing AWS CSV:', error);
        setAWSUploadStatus('error');
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setAWSMessage(`❌ ${errorMessage.replace('AWS CSV must contain columns for session_id and session_length. Found headers: ', 'Missing required columns. Found: ')}`);
      }
    };
    
    reader.onerror = () => {
      setAWSUploadStatus('error');
      setAWSMessage('❌ Error reading file');
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
        <div className="flex flex-col items-center justify-center h-96 text-gray-500 bg-gray-50 border border-gray-200 rounded">
          <div className="text-6xl mb-4">📊</div>
          <div className="text-lg font-medium mb-2">No Analysis Data</div>
          <div className="text-sm text-center max-w-md">
            Upload both Shopify and AWS CSV files, then click "Generate Fusion Report" to see charts and analytics.
          </div>
        </div>
      );
    }

    try {
      if (viewMode === 'raw') {
        return (
          <div style={{ width: '100%', height: '400px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart 
                data={fusedData}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="sessionLength"
                  type="number"
                  domain={['dataMin - 2', 'dataMax + 2']}
                />
                <YAxis 
                  domain={[0, 100]}
                />
                <Tooltip />
                <Scatter 
                  dataKey="successRate" 
                  fill="#8884d8" 
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        );
      } else {
        const smoothedData = getSmoothedData();
        
        return (
          <div style={{ width: '100%', height: '400px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart 
                data={smoothedData}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="sessionLength"
                  type="number"
                />
                <YAxis 
                  domain={[0, 100]}
                />
                <Tooltip />
                <Line 
                  dataKey="successRate" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );
      }
    } catch (error) {
      console.error('Chart rendering error:', error);
      return (
        <div className="flex items-center justify-center h-96 text-red-500 bg-red-50 border border-red-200 rounded">
          Chart rendering error: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
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
              isReportGenerated 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-600'
            }`}>
              {isReportGenerated ? '🔗 Fused Data Report' : '📝 New Session'}
            </span>
            {isReportGenerated && (
              <span className="text-gray-500">({stats.totalSessions} sessions, {stats.matchedSessions} matched)</span>
            )}
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
              
              {/* Shopify message display */}
              {shopifyMessage && (
                <div className={`text-xs p-2 rounded mt-2 ${
                  shopifyMessage.startsWith('✅') 
                    ? 'bg-green-50 text-green-700 border border-green-200' 
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}>
                  {shopifyMessage}
                </div>
              )}
              
              <div className="text-xs text-gray-600 mt-2">
                Required columns: <code>session_id</code>, <code>success</code> (or <code>success_rate</code>)<br/>
                Optional: <code>user_id</code>, <code>order_id</code>, <code>timestamp</code><br/>
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
              
              {/* AWS message display */}
              {awsMessage && (
                <div className={`text-xs p-2 rounded mt-2 ${
                  awsMessage.startsWith('✅') 
                    ? 'bg-green-50 text-green-700 border border-green-200' 
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}>
                  {awsMessage}
                </div>
              )}
              
              <div className="text-xs text-gray-600 mt-2">
                Required columns: <code>session_id</code>, <code>session_length</code><br/>
                OR: <code>session_id</code>, <code>start_timestamp</code>, <code>end_timestamp</code><br/>
                Optional: <code>user_id</code><br/>
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
              {/* Fusion message display */}
              {fusionMessage ? (
                <div className={`text-xs p-2 rounded mt-2 text-center ${
                  fusionMessage.startsWith('✅') 
                    ? 'bg-green-50 text-green-700 border border-green-200' 
                    : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                }`}>
                  {fusionMessage}
                </div>
              ) : shopifyUploadStatus !== 'success' || awsUploadStatus !== 'success' ? (
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
