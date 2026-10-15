import { useNavigate, useLocation } from 'react-router-dom';

const NAV = [
  { id: 'dashboard', path: '/dashboard', icon: '⬡', label: 'Dashboard' },
  { id: 'forecast',  path: '/forecast',  icon: '📈', label: 'Forecast' },
  { id: 'metrics',   path: '/metrics',   icon: '🎯', label: 'Metrics' },
  { id: 'holidays',  path: '/holidays',  icon: '📅', label: 'Holidays' },
  { id: 'data',      path: '/data',      icon: '🗄️', label: 'Data' },
];

export default function Sidebar({ onLogout }) {
  const navigate  = useNavigate();
  const location  = useLocation();
  const active    = location.pathname.split('/')[1];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-title">🥬 PeriShield AI</div>
        <div className="sidebar-logo-sub">Demand Forecasting Platform</div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {NAV.map(item => (
          <div
            key={item.id}
            className={`nav-item ${active === item.id ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="nav-item" style={{ color: 'var(--text-muted)', fontSize: 12 }}>
          <span className="status-dot" />
          <span>API Connected</span>
        </div>
        <div className="nav-item" onClick={onLogout} style={{ color: 'var(--accent-red)' }}>
          <span className="nav-icon">↩</span>
          <span>Logout</span>
        </div>
      </div>
    </aside>
  );
}
