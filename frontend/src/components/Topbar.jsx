const PAGE_TITLES = {
  dashboard: { title: 'Dashboard',       sub: 'System overview & live KPIs' },
  forecast:  { title: 'Demand Forecast', sub: 'Generate SKU-level demand predictions' },
  metrics:   { title: 'Model Metrics',   sub: 'Performance comparison across models' },
  holidays:  { title: 'Holiday Analysis',sub: 'Demand impact during special periods' },
  data:      { title: 'Data Management', sub: 'Upload, explore, and export datasets' },
};

export default function Topbar({ onLogout }) {
  const page   = window.location.pathname.split('/')[1] || 'dashboard';
  const info   = PAGE_TITLES[page] || PAGE_TITLES.dashboard;
  const now    = new Date().toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric' });

  return (
    <header className="topbar">
      <div>
        <div className="topbar-title">{info.title}</div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{info.sub}</div>
      </div>
      <div className="topbar-right">
        <span className="topbar-badge">RF + LSTM Hybrid</span>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{now}</span>
        <div
          style={{ width: 34, height: 34, borderRadius: '50%', background: 'var(--accent-blue)',
                   display: 'flex', alignItems: 'center', justifyContent: 'center',
                   fontSize: 14, fontWeight: 700, cursor: 'pointer' }}
          onClick={onLogout} title="Logout"
        >A</div>
      </div>
    </header>
  );
}
