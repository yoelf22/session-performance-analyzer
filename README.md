# 📊 Session Performance Analyzer

[![Deploy to GitHub Pages](https://github.com/yoelf22/session-performance-analyzer/actions/workflows/deploy.yml/badge.svg)](https://github.com/yoelf22/session-performance-analyzer/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-18.2.0-blue.svg)](https://reactjs.org/)
[![Recharts](https://img.shields.io/badge/Recharts-2.8.0-green.svg)](https://recharts.org/)

A professional, interactive web application for analyzing session performance data with advanced trend analysis, configurable smoothing, and comprehensive data visualization capabilities.

## 🚀 [Live Demo](https://yoelf22.github.io/session-performance-analyzer/)

## ✨ Features

### 📈 **Advanced Analytics**

- **Raw Data Visualization**: Interactive scatter plot showing all 200 session data points
- **Trend Analysis**: Smoothed trend lines with configurable smoothing levels (5-25 sessions)
- **Inflection Point Detection**: Automatically identifies performance transition points around session 130
- **Statistical Dashboard**: Comprehensive metrics including correlation analysis

### 🎛️ **Interactive Controls**

- **Configurable Smoothing**: Real-time adjustment of moving average window (5-25 sessions)
- **Data Export**: Export analysis results to CSV format with one click
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Professional UI**: Modern interface built with Tailwind CSS

### 📊 **Data Insights**

- **Performance Metrics**: Success rate improvement tracking over session length
- **Correlation Analysis**: Statistical correlation between session number and success rate  
- **Trend Detection**: Identifies plateau points and improvement phases
- **Comprehensive Statistics**: Mean, standard deviation, min/max values, and improvement rates

### 🔧 **Technical Excellence**

- **Error Boundaries**: Robust error handling with user-friendly fallbacks
- **Performance Monitoring**: Web Vitals integration for performance tracking
- **SEO Optimized**: Complete meta tags, structured data, and social media integration
- **Accessibility**: WCAG compliant with keyboard navigation and screen reader support

## 🛠️ Technology Stack

- **Frontend Framework**: React 18.2.0 + TypeScript
- **Data Visualization**: Recharts 2.8.0  
- **Styling**: Tailwind CSS 3.3.0
- **Build Tool**: Vite
- **Deployment**: GitHub Pages with automated CI/CD
- **Performance**: Web Vitals monitoring

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

The project includes automated GitHub Pages deployment:

1. **Fork or clone** this repository
2. **Enable GitHub Pages** in repository settings
3. **Push to main branch** - deployment happens automatically
4. **Access your site** at `https://yoelf22.github.io/session-performance-analyzer/`

### Manual Deployment

```bash
# Deploy to GitHub Pages
npm run deploy
```

## 📊 Data Analysis Features

### Session Data Generation

The analyzer generates realistic session performance data with:

- **200 sample sessions** with natural variation and noise
- **Inflection point** around session 130 where improvement rate changes
- **Two-phase performance curve**: rapid improvement (0-130) and plateau (130+)
- **Realistic noise**: ±7.5% variation with cyclical patterns

### Statistical Analysis

Comprehensive metrics calculation including:

- **Basic Statistics**: Mean, standard deviation, min/max values
- **Performance Metrics**: Initial rate, final rate, total improvement
- **Correlation Analysis**: Pearson correlation coefficient
- **Trend Detection**: Moving average with configurable window size

### Visualization Components

- **Scatter Plot**: Raw data points with inflection point markers
- **Line Charts**: Smoothed trends with original data overlay  
- **Interactive Tooltips**: Detailed information on hover
- **Responsive Containers**: Charts adapt to screen size automatically

## 🎨 UI/UX Design

### Layout Structure

- **Header Section**: Title and description with clear hierarchy
- **Control Panel**: Smoothing controls and export functionality
- **Statistics Dashboard**: Key metrics in card-based layout
- **Charts Section**: Side-by-side visualization containers
- **Detailed Analysis**: Expandable statistics and insights

### Design System

- **Color Palette**: Professional blue/gray scheme with brand colors
- **Typography**: Clear hierarchy with proper contrast ratios
- **Spacing**: Consistent 8px grid system
- **Components**: Reusable UI elements with hover states
- **Animations**: Subtle transitions for enhanced user experience

## 🔍 Code Architecture

### Component Structure

```
src/
├── components/
│   ├── SessionAnalyzer.tsx      # Main analyzer component
│   └── ErrorBoundary.tsx        # Error handling wrapper
├── App.tsx                      # Application root with error boundary
├── App.css                      # Tailwind CSS and custom styles
└── main.tsx                     # React application entry point
```

### Key Functions

- **`generateSessionData()`**: Creates realistic performance curve data
- **`applySmoothingFilter()`**: Implements moving average smoothing
- **`detectInflectionPoint()`**: Uses second derivative analysis for trend detection
- **`calculateStatistics()`**: Computes comprehensive performance metrics
- **`exportToCSV()`**: Handles data export with proper formatting

## 📈 Performance Optimization

### Loading Performance

- **Code Splitting**: Automatic chunk splitting by Vite
- **Resource Preloading**: Critical resources loaded early
- **Image Optimization**: Optimized icons and assets
- **Bundle Analysis**: Vite bundle analyzer integration

### Runtime Performance

- **React.memo**: Memoization for expensive calculations
- **useCallback**: Optimized event handlers and functions
- **Efficient Re-renders**: Strategic state management
- **Responsive Charts**: Recharts with responsive containers

## 🧪 Testing

### Running Tests

```bash
# Run test suite
npm run test

# Run tests with coverage
npm run test:coverage
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

### Getting Help

- **Documentation**: Check this README
- **Issues**: Open a [GitHub issue](https://github.com/yoelf22/session-performance-analyzer/issues)
- **Discussions**: Join [GitHub Discussions](https://github.com/yoelf22/session-performance-analyzer/discussions)

### Bug Reports

When reporting bugs, please include:

- **Browser and version**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Console errors (if any)**
- **Screenshots (if applicable)**

## 📊 Analytics & Insights

The Session Performance Analyzer is designed based on real-world session analysis patterns:

### Performance Curve Model

- **Phase 1 (Sessions 1-130)**: Rapid improvement phase with steep learning curve
- **Phase 2 (Sessions 130+)**: Plateau phase with diminishing returns
- **Realistic Variation**: Natural noise and cyclical patterns in data
- **Inflection Detection**: Mathematical identification of curve transition points

### Statistical Validity

- **Sample Size**: 200 sessions provide statistical significance
- **Correlation Analysis**: Pearson correlation coefficient calculation
- **Trend Analysis**: Moving average smoothing with configurable windows
- **Outlier Handling**: Robust statistics that handle data variation

---

## 🎯 Quick Start Guide

1. **Visit the [live demo](https://yoelf22.github.io/session-performance-analyzer/)**
2. **Adjust smoothing level** using the slider (5-25 sessions)
3. **Explore the charts** with interactive tooltips and zoom
4. **Review statistics** in the comprehensive dashboard
5. **Export data** to CSV for further analysis

---

Built with ❤️ by Yoel Frischoff | [View on GitHub](https://github.com/yoelf22/session-performance-analyzer)
