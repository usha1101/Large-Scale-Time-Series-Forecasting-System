import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LineChart, Line, Legend
} from 'recharts';

const HOLIDAYS_2025 = [
  { name:"New Year's Day",      date:'2025-01-01', category:'Federal', liftPct:12, prePct:22, postPct:8   },
  { name:'MLK Day',             date:'2025-01-20', category:'Federal', liftPct:5,  prePct:8,  postPct:3   },
  { name:"Valentine's Day",     date:'2025-02-14', category:'Special', liftPct:35, prePct:48, postPct:10  },
  { name:'St. Patrick\'s Day',  date:'2025-03-17', category:'Cultural',liftPct:18, prePct:25, postPct:6   },
  { name:'Easter',              date:'2025-04-20', category:'Religious',liftPct:28, prePct:40, postPct:12  },
  { name:'Memorial Day',        date:'2025-05-26', category:'Federal', liftPct:22, prePct:30, postPct:9   },
  { name:'Mother\'s Day',       date:'2025-05-11', category:'Special', liftPct:42, prePct:55, postPct:8   },
  { name:'Father\'s Day',       date:'2025-06-15', category:'Special', liftPct:25, prePct:32, postPct:7   },
  { name:'4th of July',         date:'2025-07-04', category:'Federal', liftPct:30, prePct:38, postPct:5   },
  { name:'Labor Day',           date:'2025-09-01', category:'Federal', liftPct:20, prePct:28, postPct:8   },
  { name:'Halloween',           date:'2025-10-31', category:'Cultural', liftPct:38, prePct:50, postPct:6  },
  { name:'Thanksgiving',        date:'2025-11-27', category:'Federal', liftPct:65, prePct:85, postPct:20  },
  { name:'Black Friday',        date:'2025-11-28', category:'Shopping', liftPct:80, prePct:10, postPct:15 },
  { name:'Christmas Eve',       date:'2025-12-24', category:'Federal', liftPct:55, prePct:70, postPct:25  },
  { name:'Christmas',           date:'2025-12-25', category:'Federal', liftPct:45, prePct:75, postPct:30  },
  { name:"New Year's Eve",      date:'2025-12-31', category:'Federal', liftPct:28, prePct:35, postPct:4   },
];

const CATEGORY_LIFT = [
  { category:'Floral',   valentines:420, thanksgiving:80,  christmas:180 },
  { category:'Bakery',   valentines:55,  thanksgiving:160, christmas:120 },
  { category:'Produce',  valentines:30,  thanksgiving:130, christmas:85  },
  { category:'Dairy',    valentines:25,  thanksgiving:90,  christmas:70  },
  { category:'Meat',     valentines:45,  thanksgiving:200, christmas:150 },
  { category:'Beverages',valentines:20,  thanksgiving:55,  christmas:40  },
];

const WEEK_WINDOW = Array.from({ length:15 }, (_, i) => ({
  day: i - 7,
  label: i===7 ? 'HOL' : i<7 ? `D-${7-i}` : `D+${i-7}`,
  dairy:    70 + (i===7?30:i===6?18:i===8?12:Math.random()*10),
  bakery:   55 + (i===7?38:i===6?22:i===8?15:Math.random()*10),
  produce:  90 + (i===7?45:i===6?28:i===8?18:Math.random()*15),
}));

const COLORS = { Federal:'#4f9cf9', Special:'#f87171', Religious:'#a78bfa', Cultural:'#fbbf24', Shopping:'#34d399' };

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:'var(--bg-card)', border:'1px solid var(--border)',
                  borderRadius:10, padding:'12px 16px', boxShadow:'var(--shadow-card)' }}>
      <div style={{ fontWeight:600, marginBottom:8, color:'var(--accent-yellow)' }}>🎉 {label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ display:'flex', justifyContent:'space-between', gap:20, marginTop:4 }}>
          <span style={{ color:'var(--text-muted)', fontSize:12 }}>{p.name}</span>
          <span style={{ color:p.fill||p.color, fontWeight:700, fontFamily:'var(--font-mono)' }}>
            {typeof p.value==='number'?`+${p.value}%`:'--'}
          </span>
        </div>
      ))}
    </div>
  );
};

export default function HolidayAnalysis() {
  const [selected, setSelected] = useState(null);
  const [filter, setFilter]     = useState('All');
  const [tab, setTab]           = useState('lift');

  const categories = ['All', ...new Set(HOLIDAYS_2025.map(h => h.category))];
  const filtered   = filter === 'All' ? HOLIDAYS_2025 : HOLIDAYS_2025.filter(h => h.category === filter);
  const liftData   = [...filtered].sort((a,b) => b.liftPct - a.liftPct).slice(0,10);

  const selHol = selected ? HOLIDAYS_2025.find(h => h.name === selected) : null;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Holiday Demand Analysis</div>
        <div className="page-subtitle">Demand uplift patterns across {HOLIDAYS_2025.length} key dates in 2025</div>
      </div>

      {/* Summary stats */}
      <div className="stat-grid" style={{ marginBottom:24 }}>
        {[
          { label:'Total Holidays',    val:HOLIDAYS_2025.length, color:'var(--accent-yellow)', icon:'📅' },
          { label:'Avg Demand Lift',   val:`+${Math.round(HOLIDAYS_2025.reduce((s,h)=>s+h.liftPct,0)/HOLIDAYS_2025.length)}%`, color:'var(--accent-green)', icon:'📈' },
          { label:'Peak Holiday',      val:'Thanksgiving', color:'var(--accent-orange)', icon:'🦃' },
          { label:'Peak Lift',         val:'+80%', color:'var(--accent-red)', icon:'🔥' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div style={{ fontSize:24 }}>{s.icon}</div>
            <div>
              <div className="stat-label">{s.label}</div>
              <div style={{ fontSize:20, fontWeight:700, color:s.color }}>{s.val}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="tabs">
        {[
          { id:'lift',     label:'📊 Demand Lift' },
          { id:'category', label:'🏪 By Category' },
          { id:'window',   label:'🕐 Event Window' },
          { id:'calendar', label:'📅 Calendar' },
        ].map(t => <div key={t.id} className={`tab ${tab===t.id?'active':''}`} onClick={() => setTab(t.id)}>{t.label}</div>)}
      </div>

      {tab === 'lift' && (
        <>
          {/* Filter */}
          <div style={{ display:'flex', gap:8, marginBottom:18, flexWrap:'wrap' }}>
            {categories.map(c => (
              <button key={c} className={`btn btn-sm ${filter===c?'btn-primary':'btn-secondary'}`}
                onClick={() => setFilter(c)} style={filter===c&&c!=='All'?{background:COLORS[c]||'var(--accent-blue)'}:{}}>
                {c}
              </button>
            ))}
          </div>

          <div className="grid-2" style={{ marginBottom:20 }}>
            <div className="chart-container" style={{ gridColumn:'span 1' }}>
              <div className="chart-header">
                <div className="chart-title">Demand Lift by Holiday</div>
                <div className="badge badge-yellow">vs. normal day</div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={liftData} layout="vertical" margin={{ top:5, right:60, left:100, bottom:5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize:10 }} unit="%" domain={[0,100]} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize:11 }} width={95} />
                  <Tooltip formatter={v => [`+${v}%`]} contentStyle={{ background:'var(--bg-card)', border:'1px solid var(--border)' }} />
                  <Bar dataKey="liftPct" name="Day-of Lift" radius={[0,4,4,0]}
                       label={{ position:'right', formatter:v=>`+${v}%`, fontSize:11, fill:'var(--text-muted)' }}>
                    {liftData.map((h,i) => <Cell key={i} fill={COLORS[h.category]||'#4f9cf9'} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Pre/Post comparison */}
            <div className="chart-container">
              <div className="chart-header">
                <div className="chart-title">Pre / Post Holiday Lift</div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={liftData.slice(0,8)} margin={{ top:5, right:10, left:-20, bottom:30 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize:9 }} angle={-30} textAnchor="end" />
                  <YAxis tick={{ fontSize:10 }} unit="%" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize:11, color:'var(--text-secondary)' }} />
                  <Bar dataKey="prePct"  name="Day Before" fill="#fbbf24" radius={[4,4,0,0]} />
                  <Bar dataKey="liftPct" name="Holiday Day" fill="#4f9cf9" radius={[4,4,0,0]} />
                  <Bar dataKey="postPct" name="Day After"  fill="#34d399" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {tab === 'category' && (
        <div className="chart-container">
          <div className="chart-header">
            <div className="chart-title">Category-Specific Holiday Lift</div>
            <div className="badge badge-purple">Selected holidays</div>
          </div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={CATEGORY_LIFT} margin={{ top:5, right:10, left:-10, bottom:0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" tick={{ fontSize:11 }} />
              <YAxis tick={{ fontSize:10 }} unit="%" />
              <Tooltip formatter={v=>[`+${v}%`]} contentStyle={{ background:'var(--bg-card)', border:'1px solid var(--border)' }} />
              <Legend wrapperStyle={{ fontSize:12, color:'var(--text-secondary)' }} />
              <Bar dataKey="valentines"   name="Valentine's Day" fill="#f87171" radius={[4,4,0,0]} />
              <Bar dataKey="thanksgiving" name="Thanksgiving"    fill="#fbbf24" radius={[4,4,0,0]} />
              <Bar dataKey="christmas"    name="Christmas"       fill="#4f9cf9" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {tab === 'window' && (
        <div className="chart-container">
          <div className="chart-header">
            <div className="chart-title">7-Day Event Window (Before & After Holiday)</div>
            <div className="badge badge-yellow">🎉 Day 0 = Holiday</div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={WEEK_WINDOW} margin={{ top:5, right:10, left:-20, bottom:0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize:11 }} />
              <YAxis tick={{ fontSize:10 }} />
              <Tooltip contentStyle={{ background:'var(--bg-card)', border:'1px solid var(--border)' }} />
              <Legend wrapperStyle={{ fontSize:12 }} />
              <Line type="monotone" dataKey="dairy"   stroke="#4f9cf9" strokeWidth={2.5} dot={d => d.payload.label==='HOL' ? <circle cx={d.cx} cy={d.cy} r={5} fill="#fbbf24" /> : false} />
              <Line type="monotone" dataKey="bakery"  stroke="#a78bfa" strokeWidth={2.5} dot={false} />
              <Line type="monotone" dataKey="produce" stroke="#34d399" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {tab === 'calendar' && (
        <>
          <div className="holiday-strip">
            🌟 Holidays with high demand lift are automatically flagged in forecast outputs
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Holiday</th><th>Date</th><th>Category</th><th>Day-Of Lift</th><th>Pre-Holiday Lift</th><th>Post Lift</th></tr>
              </thead>
              <tbody>
                {HOLIDAYS_2025.map(h => (
                  <tr key={h.name} style={{ cursor:'pointer' }}
                      onClick={() => setSelected(selected===h.name ? null : h.name)}>
                    <td><strong>{selected===h.name ? '► ' : ''}{h.name}</strong></td>
                    <td style={{ fontFamily:'var(--font-mono)', color:'var(--text-muted)' }}>{h.date}</td>
                    <td><span className="badge" style={{ background:`${COLORS[h.category]}22`, color:COLORS[h.category]||'var(--accent-blue)' }}>{h.category}</span></td>
                    <td style={{ fontFamily:'var(--font-mono)', color: h.liftPct>=50 ? 'var(--accent-red)' : h.liftPct>=25 ? 'var(--accent-orange)' : 'var(--accent-green)', fontWeight:700 }}>+{h.liftPct}%</td>
                    <td style={{ fontFamily:'var(--font-mono)', color:'var(--accent-yellow)' }}>+{h.prePct}%</td>
                    <td style={{ fontFamily:'var(--font-mono)', color:'var(--text-muted)' }}>+{h.postPct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
