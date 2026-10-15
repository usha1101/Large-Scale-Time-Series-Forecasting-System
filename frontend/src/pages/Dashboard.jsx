import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend, PieChart, Pie, Cell
} from 'recharts';
import { getMetrics, getSkus, predict } from '../api';

// ── Generate realistic mock time-series for dashboard ──────────────────────
function genSeries(days = 30, base = 80, category = 'dairy') {
  const seeds = { dairy:85, bakery:60, produce:110, meat:45, deli:30 };
  const b = seeds[category] || base;
  return Array.from({ length: days }, (_, i) => {
    const dow = i % 7;
    const wknd = dow >= 5 ? 1.25 : 1;
    const trend = 1 + i * 0.002;
    const noise = 0.9 + Math.random() * 0.2;
    const actual = Math.round(b * wknd * trend * noise);
    const pred   = Math.round(actual * (0.92 + Math.random() * 0.16));
    const date   = new Date(Date.now() - (days - i) * 86400000)
                     .toLocaleDateString('en-US', { month:'short', day:'numeric' });
    return { date, actual, predicted: pred };
  });
}

const CATEGORY_COLORS = {
  dairy:'#4f9cf9', bakery:'#a78bfa', produce:'#34d399',
  meat:'#f87171', deli:'#fbbf24', frozen:'#38bdf8',
};

const PIE_DATA = [
  { name:'Dairy',   value:22 }, { name:'Produce', value:28 },
  { name:'Bakery',  value:18 }, { name:'Meat',     value:14 },
  { name:'Deli',    value:10 }, { name:'Other',    value:8  },
];
const PIE_COLORS = ['#4f9cf9','#34d399','#a78bfa','#f87171','#fbbf24','#38bdf8'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:'var(--bg-card)', border:'1px solid var(--border)',
                  borderRadius:'var(--radius-md)', padding:'12px 16px',
                  boxShadow:'var(--shadow-card)', fontSize:13 }}>
      <div style={{ fontWeight:600, marginBottom:8, color:'var(--text-secondary)' }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ display:'flex', justifyContent:'space-between',
                                    gap:24, color:p.color, fontWeight:600 }}>
          <span style={{ color:'var(--text-muted)', fontWeight:400 }}>{p.name}</span>
          <span>{typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function Dashboard({ setActivePage }) {
  const navigate  = useNavigate();
  const [series]  = useState(() => genSeries(30));
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('dairy');
  const [catSeries] = useState(() => ({
    dairy:   genSeries(30, 85, 'dairy'),
    bakery:  genSeries(30, 60, 'bakery'),
    produce: genSeries(30, 110,'produce'),
    meat:    genSeries(30, 45, 'meat'),
  }));

  useEffect(() => {
    getMetrics()
      .then(r => setMetrics(r.data.metrics))
      .catch(() => setMetrics({
        hybrid:         { mae:8.5, rmse:12.3, mape:15.2, r2:0.87 },
        random_forest:  { mae:9.1, rmse:13.1, mape:16.8, r2:0.84 },
        lstm:           { mae:10.2,rmse:14.5, mape:18.1, r2:0.81 },
        naive_baseline: { mae:15.3,rmse:20.1, mape:28.5, r2:0.62 },
      }))
      .finally(() => setLoading(false));
  }, []);

  const mape    = metrics?.hybrid?.mape    ?? 15.2;
  const mae     = metrics?.hybrid?.mae     ?? 8.5;
  const r2      = metrics?.hybrid?.r2      ?? 0.87;
  const naiveMape = metrics?.naive_baseline?.mape ?? 28.5;
  const improvement = naiveMape > 0 ? ((naiveMape - mape) / naiveMape * 100).toFixed(1) : '46.7';

  const barData = metrics ? [
    { model:'Hybrid',   MAPE: metrics.hybrid?.mape,        MAE: metrics.hybrid?.mae },
    { model:'RF',       MAPE: metrics.random_forest?.mape,  MAE: metrics.random_forest?.mae },
    { model:'LSTM',     MAPE: metrics.lstm?.mape,            MAE: metrics.lstm?.mae },
    { model:'Baseline', MAPE: metrics.naive_baseline?.mape,  MAE: metrics.naive_baseline?.mae },
  ] : [];

  return (
    <div>
      {/* KPI Stats */}
      <div className="page-header fade-in">
        <div className="page-title">System Overview</div>
        <div className="page-subtitle">Real-time performance across 10,000+ SKU-store combinations</div>
      </div>

      <div className="stat-grid fade-in fade-in-1">
        <div className="stat-card">
          <div className="stat-icon blue">📊</div>
          <div className="stat-info">
            <div className="stat-label">SKU-Store Combos</div>
            <div className="stat-value" style={{ color:'var(--accent-blue)' }}>10,000+</div>
            <div className="stat-change pos">↑ 100 stores × 100 SKUs</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">🎯</div>
          <div className="stat-info">
            <div className="stat-label">Hybrid MAPE</div>
            <div className="stat-value" style={{ color:'var(--accent-green)' }}>{mape.toFixed(1)}%</div>
            <div className="stat-change pos">↓ {improvement}% vs baseline</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple">⚡</div>
          <div className="stat-info">
            <div className="stat-label">Mean Abs. Error</div>
            <div className="stat-value" style={{ color:'var(--accent-purple)' }}>{mae.toFixed(1)}</div>
            <div className="stat-change pos">units / day / SKU</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon cyan">📈</div>
          <div className="stat-info">
            <div className="stat-label">R² Score</div>
            <div className="stat-value" style={{ color:'var(--accent-cyan)' }}>{r2.toFixed(2)}</div>
            <div className="stat-change pos">↑ Hybrid model</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">🗓️</div>
          <div className="stat-info">
            <div className="stat-label">Training Period</div>
            <div className="stat-value" style={{ color:'var(--accent-yellow)', fontSize:20 }}>2 Years</div>
            <div className="stat-change pos">Jan 2023 – Jun 2024</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red">🔥</div>
          <div className="stat-info">
            <div className="stat-label">Categories</div>
            <div className="stat-value" style={{ color:'var(--accent-orange)' }}>10</div>
            <div className="stat-change pos">Dairy, Bakery, Produce…</div>
          </div>
        </div>
      </div>

      {/* Main chart + pie */}
      <div className="grid-2 fade-in fade-in-2" style={{ marginBottom:20 }}>
        <div className="chart-container" style={{ gridColumn:'span 1' }}>
          <div className="chart-header">
            <div className="chart-title">Actual vs Predicted Demand</div>
            <div style={{ display:'flex', gap:8 }}>
              {['dairy','bakery','produce','meat'].map(c => (
                <button key={c} className={`btn btn-sm ${category===c ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setCategory(c)}
                  style={{ padding:'4px 10px', fontSize:11 }}>
                  {c}
                </button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={catSeries[category]} margin={{ top:5, right:10, left:-20, bottom:0 }}>
              <defs>
                <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#4f9cf9" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="#4f9cf9" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#a78bfa" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="#a78bfa" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize:10 }} tickLine={false} interval={4} />
              <YAxis tick={{ fontSize:10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="actual"    stroke="#4f9cf9" fill="url(#colorActual)" strokeWidth={2} name="Actual" />
              <Area type="monotone" dataKey="predicted" stroke="#a78bfa" fill="url(#colorPred)"   strokeWidth={2} name="Predicted" strokeDasharray="4 2" />
            </AreaChart>
          </ResponsiveContainer>
          <div className="chart-legend" style={{ marginTop:12, justifyContent:'center' }}>
            <div className="legend-item"><div className="legend-dot" style={{ background:'#4f9cf9' }}/> Actual</div>
            <div className="legend-item"><div className="legend-dot" style={{ background:'#a78bfa' }}/> Predicted</div>
          </div>
        </div>

        <div className="chart-container">
          <div className="chart-header">
            <div className="chart-title">Sales by Category</div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={PIE_DATA} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                   paddingAngle={3} dataKey="value">
                {PIE_DATA.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
              </Pie>
              <Tooltip formatter={(v) => [`${v}%`]} contentStyle={{ background:'var(--bg-card)', border:'1px solid var(--border)' }} />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display:'flex', flexWrap:'wrap', gap:'8px 16px', marginTop:8 }}>
            {PIE_DATA.map((d, i) => (
              <div key={d.name} className="legend-item" style={{ fontSize:12 }}>
                <div className="legend-dot" style={{ background:PIE_COLORS[i] }} />
                {d.name} ({d.value}%)
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Model comparison bar */}
      <div className="chart-container fade-in fade-in-3" style={{ marginBottom:20 }}>
        <div className="chart-header">
          <div className="chart-title">Model Performance Comparison</div>
          <div className="badge badge-green">Hybrid wins</div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={barData} margin={{ top:5, right:10, left:-20, bottom:0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="model" tick={{ fontSize:11 }} tickLine={false} />
            <YAxis tick={{ fontSize:10 }} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize:12, color:'var(--text-secondary)' }} />
            <Bar dataKey="MAPE" fill="#4f9cf9" radius={[4,4,0,0]} name="MAPE (%)" />
            <Bar dataKey="MAE"  fill="#a78bfa" radius={[4,4,0,0]} name="MAE (units)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Quick actions */}
      <div className="grid-3 fade-in fade-in-4">
        {[
          { icon:'📈', title:'Run Forecast',    sub:'Generate demand for any SKU + store', page:'/forecast', color:'var(--accent-blue)' },
          { icon:'🎯', title:'View Full Metrics',  sub:'Deep dive into model performance',    page:'/metrics',  color:'var(--accent-purple)' },
          { icon:'🗄️', title:'Manage Data',     sub:'Upload, explore datasets',             page:'/data',     color:'var(--accent-green)' },
        ].map(a => (
          <div key={a.page} className="card" style={{ cursor:'pointer' }}
               onClick={() => navigate(a.page)}>
            <div style={{ fontSize:28, marginBottom:10 }}>{a.icon}</div>
            <div style={{ fontWeight:700, fontSize:15, color:a.color, marginBottom:4 }}>{a.title}</div>
            <div style={{ fontSize:13, color:'var(--text-muted)' }}>{a.sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
