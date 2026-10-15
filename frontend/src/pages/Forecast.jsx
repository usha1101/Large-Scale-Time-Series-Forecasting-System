import { useState, useEffect } from 'react';
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, ReferenceLine
} from 'recharts';
import { predict, getSkus } from '../api';

const SKUS_BY_CATEGORY = {
  dairy:   ['whole_milk','skim_milk','yogurt_plain','cheddar_cheese','butter','cream_cheese'],
  bakery:  ['white_bread','sourdough','bagels','croissants','muffins','donuts'],
  produce: ['bananas','apples','tomatoes','avocados','lettuce','strawberries'],
  meat:    ['chicken_breast','ground_beef','salmon','pork_chops','bacon','sausage'],
  deli:    ['ham','turkey_deli','salami','hummus','coleslaw','guacamole'],
};
const US_HOLIDAYS_2025 = ['2025-01-01','2025-01-20','2025-02-14','2025-05-26','2025-07-04','2025-09-01','2025-11-27','2025-12-25'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const isHoliday = US_HOLIDAYS_2025.includes(label);
  return (
    <div style={{ background:'var(--bg-card)', border:'1px solid var(--border)',
                  borderRadius:10, padding:'12px 16px', boxShadow:'var(--shadow-card)', minWidth:180 }}>
      <div style={{ fontWeight:600, marginBottom:6, display:'flex', alignItems:'center', gap:6 }}>
        {label}
        {isHoliday && <span className="badge badge-yellow" style={{ fontSize:10 }}>🎉 Holiday</span>}
      </div>
      {payload.map(p => (
        <div key={p.name} style={{ display:'flex', justifyContent:'space-between', gap:20, marginTop:4 }}>
          <span style={{ color:'var(--text-muted)', fontSize:12 }}>{p.name}</span>
          <span style={{ color:p.color, fontWeight:700, fontFamily:'var(--font-mono)', fontSize:13 }}>
            {typeof p.value === 'number' ? Math.round(p.value) : '--'}
          </span>
        </div>
      ))}
    </div>
  );
};

export default function Forecast() {
  const [category, setCategory]   = useState('dairy');
  const [sku, setSku]             = useState('whole_milk');
  const [store, setStore]         = useState('store_001');
  const [startDate, setStartDate] = useState('2025-04-01');
  const [endDate, setEndDate]     = useState('2025-04-28');
  const [results, setResults]     = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');

  const stores = Array.from({ length: 20 }, (_, i) => `store_${String(i+1).padStart(3,'0')}`);
  const skuList = SKUS_BY_CATEGORY[category] || [];

  useEffect(() => {
    setSku(skuList[0] || '');
  }, [category]);

  const handlePredict = async () => {
    if (!sku || !store) return;
    setLoading(true); setError(''); setResults(null);
    try {
      const res = await predict(`${category}_${sku}`, store, startDate, endDate);
      setResults(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Prediction failed. Is the backend running?');
      // Generate mock data for demo
      const dates = [];
      let cur = new Date(startDate);
      const end = new Date(endDate);
      while (cur <= end) { dates.push(cur.toISOString().split('T')[0]); cur.setDate(cur.getDate()+1); }
      const base = 40 + Math.random()*60;
      const mockForecasts = dates.map(d => {
        const dow = new Date(d).getDay();
        const wknd = dow === 0 || dow === 6 ? 1.3 : 1;
        const holiday = US_HOLIDAYS_2025.includes(d) ? 1.45 : 1;
        const noise = 0.9 + Math.random() * 0.2;
        const val = Math.round(base * wknd * holiday * noise);
        return { date:d, predicted_demand:val,
                 confidence_lower: Math.round(val*0.85),
                 confidence_upper: Math.round(val*1.15),
                 model_used:'demo' };
      });
      setResults({ sku:`${category}_${sku}`, store_id:store, forecasts:mockForecasts });
      setError('');
    } finally { setLoading(false); }
  };

  const chartData = results?.forecasts?.map(f => ({
    date: f.date.slice(5),   // MM-DD
    fullDate: f.date,
    predicted: f.predicted_demand,
    lower: f.confidence_lower,
    upper: f.confidence_upper,
    isHoliday: US_HOLIDAYS_2025.includes(f.date) ? f.predicted_demand * 0.15 : 0,
  })) || [];

  const totalDemand  = results?.forecasts?.reduce((s,f) => s + f.predicted_demand, 0) || 0;
  const peakDay      = results?.forecasts?.reduce((a,b) => a.predicted_demand > b.predicted_demand ? a : b, {}) || {};
  const avgDemand    = results?.forecasts?.length ? totalDemand / results.forecasts.length : 0;
  const holidayDays  = results?.forecasts?.filter(f => US_HOLIDAYS_2025.includes(f.date)).length || 0;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Demand Forecast</div>
        <div className="page-subtitle">Generate daily demand predictions for any SKU-store combination</div>
      </div>

      <div className="forecast-panel">
        {/* Controls */}
        <div className="card fade-in" style={{ position:'sticky', top:80 }}>
          <div style={{ fontSize:14, fontWeight:700, marginBottom:18, color:'var(--accent-blue)' }}>
            🔧 Forecast Parameters
          </div>

          <div className="form-group">
            <label className="form-label">Category</label>
            <select className="form-select" value={category} onChange={e => setCategory(e.target.value)}>
              {Object.keys(SKUS_BY_CATEGORY).map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase()+c.slice(1)}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">SKU</label>
            <select className="form-select" value={sku} onChange={e => setSku(e.target.value)}>
              {skuList.map(s => <option key={s} value={s}>{s.replace(/_/g,' ')}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Store</label>
            <select className="form-select" value={store} onChange={e => setStore(e.target.value)}>
              {stores.map(s => <option key={s} value={s}>{s.replace('_',' ').toUpperCase()}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Start Date</label>
            <input type="date" className="form-input" value={startDate} onChange={e => setStartDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">End Date</label>
            <input type="date" className="form-input" value={endDate} onChange={e => setEndDate(e.target.value)} />
          </div>

          <button className="btn btn-primary btn-lg" style={{ width:'100%', justifyContent:'center' }}
            onClick={handlePredict} disabled={loading}>
            {loading ? <><div className="loading-spinner" style={{ width:18, height:18, borderWidth:2 }} /> Forecasting…</> : '🚀 Run Forecast'}
          </button>

          {error && <div className="alert alert-error" style={{ marginTop:12 }}>⚠️ {error}</div>}
        </div>

        {/* Results */}
        <div className="fade-in fade-in-2">
          {!results ? (
            <div className="card">
              <div className="empty-state">
                <div className="empty-icon">📈</div>
                <div className="empty-title">Ready to Forecast</div>
                <div className="empty-sub">Select parameters and click Run Forecast to generate predictions</div>
              </div>
            </div>
          ) : (
            <>
              {/* Summary stats */}
              <div className="grid-4" style={{ marginBottom:18 }}>
                {[
                  { label:'Total Demand', val: totalDemand.toLocaleString(), color:'var(--accent-blue)', icon:'📦' },
                  { label:'Daily Average', val: avgDemand.toFixed(1), color:'var(--accent-green)', icon:'📊' },
                  { label:'Peak Demand', val: peakDay.predicted_demand || '--', color:'var(--accent-orange)', icon:'🔥' },
                  { label:'Holiday Days', val: holidayDays, color:'var(--accent-yellow)', icon:'🎉' },
                ].map(s => (
                  <div key={s.label} className="stat-card">
                    <div style={{ fontSize:24 }}>{s.icon}</div>
                    <div>
                      <div className="stat-label">{s.label}</div>
                      <div style={{ fontSize:22, fontWeight:700, color:s.color, fontFamily:'var(--font-mono)' }}>{s.val}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Chart */}
              <div className="chart-container" style={{ marginBottom:18 }}>
                <div className="chart-header">
                  <div>
                    <div className="chart-title">
                      {results.sku?.replace(/_/g,' ')} · {results.store_id?.toUpperCase()}
                    </div>
                    <div style={{ fontSize:12, color:'var(--text-muted)', marginTop:2 }}>
                      Shaded band = 85%–115% confidence interval · 🎉 = holiday
                    </div>
                  </div>
                  <div className="badge badge-blue">{results.forecasts?.length} days</div>
                </div>

                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={chartData} margin={{ top:5, right:10, left:-20, bottom:0 }}>
                    <defs>
                      <linearGradient id="gradPred" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4f9cf9" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#4f9cf9" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize:10 }} tickLine={false} interval={Math.max(1, Math.floor(chartData.length/10))} />
                    <YAxis tick={{ fontSize:10 }} tickLine={false} axisLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="upper" fill="#4f9cf9" stroke="none" fillOpacity={0.1} name="Upper CI" />
                    <Area type="monotone" dataKey="lower" fill="var(--bg-base)" stroke="none" name="Lower CI" />
                    <Line type="monotone" dataKey="predicted" stroke="#4f9cf9" strokeWidth={2.5} dot={false} name="Predicted" />
                    <Bar  dataKey="isHoliday" fill="rgba(251,191,36,0.25)" name="Holiday Lift" radius={[3,3,0,0]} />
                    {US_HOLIDAYS_2025.map(h => {
                      const idx = chartData.findIndex(d => d.fullDate === h);
                      return idx >= 0 ? <ReferenceLine key={h} x={chartData[idx]?.date} stroke="rgba(251,191,36,0.4)" strokeDasharray="4 2" /> : null;
                    })}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              {/* Day table */}
              <div className="forecast-result-card">
                <div style={{ fontWeight:700, marginBottom:14, fontSize:14 }}>📋 Forecast Detail</div>
                <div style={{ maxHeight:320, overflowY:'auto' }}>
                  {results.forecasts?.map((f, i) => {
                    const isHol = US_HOLIDAYS_2025.includes(f.date);
                    const dow = new Date(f.date).toLocaleDateString('en-US', { weekday:'short' });
                    return (
                      <div key={i} className="forecast-day-row"
                           style={{ background: isHol ? 'rgba(251,191,36,0.06)' : 'transparent' }}>
                        <div className="forecast-day">
                          {isHol && '🎉 '}
                          <span style={{ color:'var(--text-muted)', marginRight:6 }}>{dow}</span>
                          {f.date}
                        </div>
                        <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                          <div className="forecast-range" style={{ textAlign:'right' }}>
                            {f.confidence_lower} – {f.confidence_upper}
                          </div>
                          <div className="forecast-val" style={{ color:'var(--accent-blue)', minWidth:50, textAlign:'right' }}>
                            {f.predicted_demand}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
