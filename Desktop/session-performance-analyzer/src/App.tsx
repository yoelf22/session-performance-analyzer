import ErrorBoundary from './components/ErrorBoundary';
import SessionAnalyzer from './components/SessionAnalyzer';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <SessionAnalyzer />
    </ErrorBoundary>
  );
}

export default App;
