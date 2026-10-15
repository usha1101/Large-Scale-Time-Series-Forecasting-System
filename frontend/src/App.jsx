import { useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Forecast from './pages/Forecast';
import MetricsPage from './pages/MetricsPage';
import HolidayAnalysis from './pages/HolidayAnalysis';
import DataManagement from './pages/DataManagement';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [currentPage, setCurrentPage] = useState('dashboard');

  const handleLogin = (newToken) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          🥬 PeriShield AI
        </div>
        <nav className="nav-menu">
          <div className="nav-group">Main</div>
          <button className={`nav-item ${currentPage === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentPage('dashboard')}>
            📊 Dashboard
          </button>
          <button className={`nav-item ${currentPage === 'explorer' ? 'active' : ''}`}
            onClick={() => setCurrentPage('explorer')}>
            🔍 Predictions
          </button>
          
          <div className="nav-group">Analysis</div>
          <button className={`nav-item ${currentPage === 'metrics' ? 'active' : ''}`}
            onClick={() => setCurrentPage('metrics')}>
            📈 Model Metrics
          </button>
          <button className={`nav-item ${currentPage === 'holidays' ? 'active' : ''}`}
            onClick={() => setCurrentPage('holidays')}>
            🎉 Holiday Lift
          </button>
          
          <div className="nav-group">System</div>
          <button className={`nav-item ${currentPage === 'data' ? 'active' : ''}`}
            onClick={() => setCurrentPage('data')}>
            🗄️ Data Management
          </button>
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontSize: 13, marginBottom: 8 }}>
            Admin User <span className="badge badge-green">Online</span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={handleLogout} style={{ width: '100%' }}>
            🚪 Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content fade-in">
        <div className="topbar">
          <div style={{ flex: 1 }}></div>
          <div className="badge badge-blue">Hybrid RF+LSTM Active</div>
          <div className="badge badge-green">Model loaded</div>
        </div>
        
        <div className="page-content fade-in">
          {currentPage === 'dashboard' && <Dashboard />}
          {currentPage === 'explorer' && <Forecast />}
          {currentPage === 'metrics' && <MetricsPage />}
          {currentPage === 'holidays' && <HolidayAnalysis />}
          {currentPage === 'data' && <DataManagement />}
        </div>
      </main>
    </div>
  );
}

export default App;
