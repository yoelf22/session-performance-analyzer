import ErrorBoundary from './components/ErrorBoundary';
import SessionAnalyzer from './components/SessionAnalyzerNew';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <SessionAnalyzer />
    </ErrorBoundary>
  );
}

export default App;
