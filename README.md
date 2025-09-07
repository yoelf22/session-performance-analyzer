# 📊 Session Performance Analyzer

[![Deploy to GitHub Pages](https://github.com/yoelf22/session-performance-analyzer/actions/workflows/deploy.yml/badge.svg)](https://github.com/yoelf22/session-performance-analyzer/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-19.1.1-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.3-blue.svg)](https://www.typescriptlang.org/)

A professional web application for analyzing e-commerce session performance by fusing Shopify success metrics with AWS session duration data to identify optimal engagement patterns and inflection points.

## 🚀 [Live Demo](https://yoelf22.github.io/session-performance-analyzer/)

## 📋 Data Requirements

### Required Input Files

The analyzer requires **two CSV files** to perform the fusion analysis:

#### 1. Shopify Data (Success Metrics)
**Purpose**: Contains session success rates or conversion data from your e-commerce platform.

**Required Columns:**
- `session_id` (or `sessionid`, `session-id`) - Unique session identifier
- `success` (or `success_rate`, `success_percent`) - Success rate as decimal (0.45) or percentage (45)

**Optional Columns:**
- `user_id` - User identifier for additional analysis
- `order_id` - Order identifier for transaction tracking
- `timestamp` - Session timestamp for temporal analysis

**Example Shopify CSV:**
```csv
session_id,user_id,success,order_id,timestamp
sess_001,user_123,0.85,order_456,2024-09-01T10:30:00Z
sess_002,user_124,0.92,order_457,2024-09-01T10:31:15Z
sess_003,user_125,0.73,,2024-09-01T10:32:30Z
```

#### 2. AWS Data (Session Lengths)
**Purpose**: Contains session duration data from your analytics platform.

**Required Columns (Option A - Direct Duration):**
- `session_id` (or `sessionid`, `session-id`) - Unique session identifier
- `session_length` (or `duration`, `session_duration`) - Duration in seconds

**Required Columns (Option B - Timestamp Calculation):**
- `session_id` - Unique session identifier  
- `start_timestamp` (or `start_time`, `begin_timestamp`) - Session start time
- `end_timestamp` (or `end_time`, `finish_timestamp`) - Session end time

**Optional Columns:**
- `user_id` - User identifier for correlation

**Example AWS CSV (Option A):**
```csv
session_id,user_id,session_length
sess_001,user_123,4.2
sess_002,user_124,6.8
sess_003,user_125,2.1
```

**Example AWS CSV (Option B):**
```csv
session_id,user_id,start_timestamp,end_timestamp
sess_001,user_123,1724526540,1724526544.2
sess_002,user_124,1724526578.8,1724526585.6
sess_003,user_125,1724526590,1724526592.1
```

### Timestamp Format Support

The analyzer supports multiple timestamp formats:
- **Unix timestamps** (seconds): `1724526540`
- **Unix timestamps** (milliseconds): `1724526540000`
- **ISO 8601**: `2024-09-01T10:30:00Z`
- **Standard formats**: `2024-09-01 10:30:00`

### Column Name Flexibility

The analyzer uses intelligent column detection and supports various naming conventions:

| Data Type | Accepted Column Names |
|-----------|----------------------|
| Session ID | `session_id`, `sessionid`, `session-id`, or any column containing "session" and "id" |
| Success Rate | `success`, `success_rate`, `success_percent`, `success_percentage` |
| Session Length | `session_length`, `duration`, `session_duration`, `length` |
| Start Time | `start_timestamp`, `start_time`, `starttime`, `begin_timestamp` |
| End Time | `end_timestamp`, `end_time`, `endtime`, `finish_timestamp` |
| User ID | `user_id`, `userid`, `user-id`, `user` |

## ✨ Features

### 📈 **Fusion Analytics**
- **Data Fusion**: Merges Shopify success metrics with AWS session duration data
- **Session Matching**: Intelligent matching by session ID with detailed match rate reporting
- **Cross-Platform Analysis**: Combines e-commerce and analytics data for comprehensive insights

### 🎯 **Inflection Point Detection**
- **Advanced Algorithm**: Uses slope change analysis to identify performance transition points
- **Mathematical Approach**: Bins data to reduce noise, calculates slope changes to find maximum curvature
- **Realistic Detection**: Accurately identifies inflection points around 5-6 seconds based on real user behavior

### 📊 **Interactive Visualizations**
- **Scatter Plot**: Shows individual session data points with success rate vs. session length
- **Trend Analysis**: Smoothed trend lines with configurable smoothing levels
- **Responsive Charts**: 500px width charts optimized for clarity and detail

### 🎛️ **Professional UI**
- **Responsive Layout**: CSS Grid-based design with mobile-first approach
- **Desktop Layout**: Side-by-side arrangement with controls left, action button right
- **Status Indicators**: Color-coded upload status with inline messaging
- **Data Export**: One-click CSV export of fusion results

## 🧮 Statistical Analysis & Algorithms

### Inflection Point Detection Algorithm

The core algorithm uses **slope change analysis** to identify the mathematical inflection point:

```typescript
// 1. Data Preparation
const sortedData = data.sort((a, b) => a.sessionLength - b.sessionLength);

// 2. Data Binning (reduces noise)
const binSize = Math.max(1, Math.floor(sortedData.length / 20));
const binnedData = groupIntoBins(sortedData, binSize);

// 3. Slope Calculation
for each point i in binnedData:
    slopeBefore = (point[i].success - point[i-1].success) / 
                  (point[i].length - point[i-1].length)
    slopeAfter = (point[i+1].success - point[i].success) / 
                 (point[i+1].length - point[i].length)
    
// 4. Maximum Slope Change Detection
maxSlopeChange = max(abs(slopeAfter - slopeBefore))
inflectionPoint = sessionLength where maxSlopeChange occurs
```

### Statistical Rationale

#### Why Slope Change Analysis?
1. **Robust to Noise**: Binning reduces individual data point variation
2. **Mathematically Sound**: Identifies true curvature changes, not arbitrary percentages
3. **Realistic Results**: Finds actual behavioral transition points around 5-6 seconds
4. **Visual Correlation**: Matches what analysts see visually in charts

#### Performance Curve Theory
- **Early Phase (0-5s)**: High engagement, rapid success rate improvement
- **Inflection Point (5-6s)**: Transition where user behavior changes
- **Late Phase (6s+)**: Declining engagement, diminishing returns

### Data Quality Metrics
- **Match Rate**: Percentage of sessions found in both datasets
- **Data Coverage**: Total sessions analyzed vs. uploaded
- **Statistical Significance**: Minimum 10 data points required for analysis

## 🛠️ Technology Stack

- **Frontend**: React 19.1.1 + TypeScript 5.8.3
- **Data Visualization**: Recharts 3.1.2
- **Styling**: Custom CSS with CSS Grid responsive layout
- **Icons**: Lucide React for consistent iconography
- **Build Tool**: Vite 7.1.2
- **Deployment**: GitHub Pages with automated CI/CD

## 📦 Installation & Setup

### Prerequisites
- Node.js 16+ 
- npm or yarn
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/yoelf22/session-performance-analyzer.git
cd session-performance-analyzer

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Build for Production

```bash
# Create optimized production build
npm run build

# Test production build locally
npm run preview
```

## 🚀 Deployment

### GitHub Pages (Automated)

```bash
# Deploy to GitHub Pages
npm run deploy
```

The project includes automated deployment configuration in `package.json`.

## 💡 Usage Guide

1. **Upload Shopify Data**: CSV file with session IDs and success rates
2. **Upload AWS Data**: CSV file with session IDs and durations/timestamps  
3. **Generate Analysis**: Click the prominent "Generate Fusion Analysis" button
4. **Review Metrics**: 
   - Total Sessions: Combined data count
   - Matched: Sessions found in both datasets
   - Inflection Point: Calculated transition point in seconds
   - Success Rates: Early vs. late phase performance
5. **Analyze Charts**: 
   - Left: Scatter plot of individual sessions
   - Right: Trend analysis with smoothing
6. **Export Results**: Download fused dataset as CSV

## 🔬 Data Processing Pipeline

### 1. CSV Parsing
- Flexible column detection with fuzzy matching
- Support for quoted values and various delimiters
- Robust error handling with detailed feedback

### 2. Data Validation
- Session ID format validation
- Numeric value parsing with range checking
- Timestamp format detection and conversion

### 3. Session Fusion
- Inner join on session_id
- Data type normalization (percentages, timestamps)
- Missing value handling

### 4. Statistical Analysis
- Inflection point calculation using slope analysis
- Success rate aggregation by session length ranges
- Performance metrics computation

## 📈 Performance Optimization

- **Efficient Data Processing**: Optimized parsing and fusion algorithms
- **Responsive UI**: CSS Grid with mobile-first responsive design
- **Chunked Bundle**: Vite optimization with code splitting
- **Memory Management**: Cleanup of large datasets after processing

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

### Getting Help
- **Documentation**: This README contains comprehensive information
- **Issues**: Open a [GitHub issue](https://github.com/yoelf22/session-performance-analyzer/issues)
- **Live Demo**: Test functionality at [live demo](https://yoelf22.github.io/session-performance-analyzer/)

### Bug Reports
Please include:
- Browser and version
- Sample data files (if possible)
- Steps to reproduce
- Expected vs actual behavior
- Console errors (if any)

## 🧪 Mock Data Generator

For testing and demonstration purposes, this repository includes a command-line tool to generate realistic sample data.

### Quick Generation

```bash
# Generate sample data files in the project directory
cd mock_data_gen
node sample_data_generator_cli.js --type both --sessions 150

# This creates:
# aws_sample_data_150s_2025-01-22.csv
# shopify_sample_data_150s_n15_2025-01-22.csv
```

### Generator Features

- **Dual Dataset Generation**: Creates matching AWS and Shopify CSV files
- **Realistic Patterns**: Configurable performance curves with inflection points
- **Noise Injection**: Adds realistic variance (default 15% noise)
- **Flexible Configuration**: Customize session count, patterns, and output files

### Usage Options

```bash
# Generate both datasets with defaults (200 sessions)
node sample_data_generator_cli.js

# Generate AWS data only with custom session count
node sample_data_generator_cli.js --type aws --sessions 100

# Generate Shopify data with custom noise level
node sample_data_generator_cli.js --type shopify --noise 0.25 --sessions 150

# Generate both with linear pattern and custom inflection point
node sample_data_generator_cli.js --pattern linear --inflection 80 --sessions 120
```

### Generated Data Format

**AWS Data** (`user_id,session_id,start_timestamp,end_timestamp`):
```csv
USER_1234,SESS_000001,1724515200,1724515201.0
USER_5678,SESS_000002,1724515260,1724515261.2
```

**Shopify Data** (`user_id,session_id,success`):
```csv
USER_1234,SESS_000001,1
USER_5678,SESS_000002,0
```

### Data Patterns

- **Session Duration**: Linear increase (1.0s + 0.2s per session)
- **Success Rate**: Exponential decay from 99% → 55% → 5% at inflection point
- **Inflection Point**: Default at session 130 (configurable)
- **Realistic Noise**: 15% random variation (configurable 0-100%)

See [`mock_data_gen/cli_readme.md`](mock_data_gen/cli_readme.md) for complete documentation.

---

## 🎯 Quick Start

### Option 1: Use Generated Sample Data
```bash
# Generate test data
cd mock_data_gen
node sample_data_generator_cli.js --sessions 150

# Upload the generated CSV files to the web app
```

### Option 2: Use Your Own Data
1. **Visit**: [https://yoelf22.github.io/session-performance-analyzer/](https://yoelf22.github.io/session-performance-analyzer/)
2. **Prepare**: Two CSV files with session data (see Data Requirements above)
3. **Upload**: Shopify file first, then AWS file
4. **Analyze**: Click "Generate Fusion Analysis"
5. **Export**: Download results for further analysis

---

Built with ❤️ for e-commerce analytics | [View on GitHub](https://github.com/yoelf22/session-performance-analyzer)