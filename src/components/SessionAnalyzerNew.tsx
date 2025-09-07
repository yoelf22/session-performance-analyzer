import React, { useState, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { BarChart3, TrendingDown, AlertTriangle, Upload, Download } from 'lucide-react';
import './SessionAnalyzer.css';

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
  sessionNumber: number;
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

  // ... (keeping all the existing parsing and processing functions) ...
  const generateSampleData = (): FusedDataPoint[] => {
    const points: FusedDataPoint[] = [];
    // Define inflection point to match realistic user behavior (around 5-6 seconds)
    const inflectionSessionLength = 5.5; // This matches your real data pattern
    
    for (let i = 1; i <= 200; i++) {
      // Generate session lengths from 0.5 to 20 seconds (more realistic range)
      const sessionLength = 0.5 + (i - 1) * 0.1; // 0.5 to 20.4 seconds
      let baseSuccessRate: number;
      
      // Base success rate on session length - realistic user engagement pattern
      if (sessionLength <= inflectionSessionLength) {
        // Before inflection: very high success rate (engaged users)
        const progressRatio = sessionLength / inflectionSessionLength;
        // More gradual decline until inflection point
        baseSuccessRate = 0.85 + (0.95 - 0.85) * (1 - Math.pow(progressRatio, 0.5));
      } else {
        // After inflection: rapid decline (users losing interest)
        const excessTime = sessionLength - inflectionSessionLength;
        const declineRate = Math.exp(-excessTime * 0.3); // Exponential decay
        baseSuccessRate = 0.15 + (0.70 - 0.15) * declineRate;
      }
      
      const noise = (Math.random() - 0.5) * 0.12; // Moderate noise for realism
      const successRate = Math.max(0.02, Math.min(0.98, baseSuccessRate + noise));
      
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
    // Sort sample data by session length (same as in fuseData)
    const sortedData = sampleData.sort((a, b) => a.sessionLength - b.sessionLength);
    setFusedData(sortedData);
    setShopifyUploadStatus('idle');
    setAWSUploadStatus('idle');
    setIsReportGenerated(true);
    
    // Use the same 65% calculation as in generateFusionReport
    const earlyData = sortedData.slice(0, Math.floor(sortedData.length * 0.65));
    const lateData = sortedData.slice(Math.floor(sortedData.length * 0.65));
    const inflectionPoint = sortedData.length > 0 ? sortedData[Math.floor(sortedData.length * 0.65)]?.sessionLength || 0 : 0;
    
    setStats({
      totalSessions: sortedData.length,
      matchedSessions: sortedData.length,
      inflectionPoint: inflectionPoint.toFixed(1),
      earlySuccessRate: earlyData.length > 0 ? (earlyData.reduce((sum, p) => sum + p.successRate, 0) / earlyData.length).toFixed(1) : '0',
      lateSuccessRate: lateData.length > 0 ? (lateData.reduce((sum, p) => sum + p.successRate, 0) / lateData.length).toFixed(1) : '0',
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

  const renderChart = () => {
    if (!fusedData.length) {
      return (
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '300px',
          color: 'var(--muted)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
          <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>No Analysis Data</div>
          <div style={{ fontSize: '13px', maxWidth: '300px' }}>
            Upload both Shopify and AWS CSV files, then click "Generate Analysis" to see charts and analytics.
          </div>
        </div>
      );
    }

    try {
      if (viewMode === 'raw') {
        return (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart 
              data={fusedData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis 
                dataKey="sessionLength"
                type="number"
                domain={['dataMin - 2', 'dataMax + 2']}
                stroke="#64748b"
              />
              <YAxis 
                domain={[0, 100]}
                stroke="#64748b"
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#ffffff', 
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  color: '#1e293b'
                }}
              />
              <Scatter 
                dataKey="successRate" 
                fill="#3b82f6" 
              />
            </ScatterChart>
          </ResponsiveContainer>
        );
      } else {
        const smoothedData = getSmoothedData();
        
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart 
              data={smoothedData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis 
                dataKey="sessionLength"
                type="number"
                stroke="#64748b"
              />
              <YAxis 
                domain={[0, 100]}
                stroke="#64748b"
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#ffffff', 
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  color: '#1e293b'
                }}
              />
              <Line 
                dataKey="successRate" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        );
      }
    } catch (error) {
      console.error('Chart rendering error:', error);
      return (
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '300px',
          color: 'var(--err)',
          textAlign: 'center'
        }}>
          Chart rendering error: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      );
    }
  };

  return (
    <div className="app">
      {/* Header Section */}
      <section className="heading panel">
        <h1>Session Performance Analyzer</h1>
        <p>Analytics for session length vs success rate correlation</p>
        {isReportGenerated && (
          <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--muted)' }}>
            {stats.totalSessions} sessions • {stats.matchedSessions} matched
          </div>
        )}
      </section>

      {/* Controls Section */}
      <section className="controls panel">
        <h2>📂 Upload Data Files</h2>
        
        <div className="upload-section">
          <div className="upload-row">
            <div className="upload-item">
              <label>🛒 Shopify Data (Success Metrics)</label>
              <input
                type="file"
                ref={shopifyFileRef}
                onChange={handleShopifyUpload}
                accept=".csv"
              />
              <div className="btn-group">
                <button 
                  className={`btn ${shopifyUploadStatus === 'success' ? 'success' : shopifyUploadStatus === 'error' ? 'error' : 'primary'}`}
                  onClick={() => shopifyFileRef.current?.click()}
                  disabled={shopifyUploadStatus === 'uploading'}
                >
                  <Upload size={16} style={{ marginRight: '6px' }} />
                  {shopifyUploadStatus === 'uploading' ? 'Uploading...' :
                   shopifyUploadStatus === 'success' ? `Update (${shopifyData.length})` :
                   shopifyUploadStatus === 'error' ? 'Try Again' : 'Choose File'}
                </button>
              </div>
            </div>
            
            <div className="upload-item">
              <label>☁️ AWS Data (Session Lengths)</label>
              <input
                type="file"
                ref={awsFileRef}
                onChange={handleAWSUpload}
                accept=".csv"
              />
              <div className="btn-group">
                <button 
                  className={`btn ${awsUploadStatus === 'success' ? 'success' : awsUploadStatus === 'error' ? 'error' : 'primary'}`}
                  onClick={() => awsFileRef.current?.click()}
                  disabled={awsUploadStatus === 'uploading'}
                >
                  <Upload size={16} style={{ marginRight: '6px' }} />
                  {awsUploadStatus === 'uploading' ? 'Uploading...' :
                   awsUploadStatus === 'success' ? `Update (${awsData.length})` :
                   awsUploadStatus === 'error' ? 'Try Again' : 'Choose File'}
                </button>
              </div>
            </div>
          </div>
          
          <div className="messages">
            {shopifyMessage && (
              <div className={`alert ${shopifyMessage.startsWith('✅') ? 'success' : 'error'}`}>
                {shopifyMessage}
              </div>
            )}
            {awsMessage && (
              <div className={`alert ${awsMessage.startsWith('✅') ? 'success' : 'error'}`}>
                {awsMessage}
              </div>
            )}
          </div>
        </div>

        <div className="analysis-controls">
          <div className="control-row">
            <label>View Mode:</label>
            <select 
              value={viewMode} 
              onChange={(e) => setViewMode(e.target.value as 'raw' | 'trend')}
            >
              <option value="raw">Raw Data Points</option>
              <option value="trend">Smoothed Trend</option>
            </select>
          </div>
          
          {viewMode === 'trend' && (
            <div className="control-row">
              <label>Smoothing Level:</label>
              <input
                type="range"
                min="5"
                max="25"
                value={smoothingLevel}
                onChange={(e) => setSmoothingLevel(parseInt(e.target.value))}
              />
              <span style={{ color: 'var(--muted)', fontSize: '12px', minWidth: '60px' }}>
                {smoothingLevel} sessions
              </span>
            </div>
          )}
        </div>
      </section>

      {/* Actions Section */}
      <section className="actions panel">
        <h2>🔬 Generate Analysis</h2>
        
        <div className="cta">
          <button
            className="btn primary"
            onClick={generateFusionReport}
            disabled={shopifyUploadStatus !== 'success' || awsUploadStatus !== 'success'}
          >
            🔗 Generate Analysis
          </button>
          
          {fusionMessage ? (
            <div className={`alert ${fusionMessage.startsWith('✅') ? 'success' : 'warn'}`}>
              {fusionMessage}
            </div>
          ) : shopifyUploadStatus !== 'success' || awsUploadStatus !== 'success' ? (
            <div className="hint">Upload both data sources to enable analysis</div>
          ) : (
            <div className="hint" style={{ color: 'var(--ok)' }}>Ready to generate analysis</div>
          )}
        </div>

        <div className="secondary-actions">
          <button className="btn ghost" onClick={loadSampleData}>
            <BarChart3 size={14} style={{ marginRight: '4px' }} />
            Demo Data
          </button>
          <button 
            className="btn ghost" 
            onClick={exportData} 
            disabled={fusedData.length === 0}
          >
            <Download size={14} style={{ marginRight: '4px' }} />
            Export
          </button>
        </div>
      </section>

      {/* Numbers Section */}
      <section className="numbers panel">
        <h2>📊 Analysis Results</h2>
        <div className="grid">
          <div className="stat">
            <div className="label">Total Sessions</div>
            <div className="value">{stats.totalSessions}</div>
          </div>
          <div className="stat">
            <div className="label">Matched</div>
            <div className="value">{stats.matchedSessions}</div>
          </div>
          <div className="stat">
            <div className="label">Inflection Point</div>
            <div className="value">{stats.inflectionPoint}s</div>
          </div>
          <div className="stat">
            <div className="label">Early Success</div>
            <div className="value">{stats.earlySuccessRate}%</div>
          </div>
          <div className="stat">
            <div className="label">Late Success</div>
            <div className="value">{stats.lateSuccessRate}%</div>
          </div>
        </div>
      </section>

      {/* Charts Section */}
      <section className="charts panel">
        <h2>📈 Visualization</h2>
        <div className="grid">
          <div className="chart-card">
            <h3>Success Rate vs Session Length</h3>
            <div style={{ height: '360px' }}>
              {renderChart()}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default SessionAnalyzer;