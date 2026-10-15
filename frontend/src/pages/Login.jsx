import { useState } from 'react';
import { login } from '../api';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const res = await login(username, password);
      onLogin(res.data.access_token);
    } catch (err) {
      // Demo: allow login even if backend is down
      if (username === 'admin' && password === 'admin123') {
        onLogin('demo-token-' + Date.now());
      } else {
        setError(err.response?.data?.detail || 'Invalid credentials. Try admin / admin123');
      }
    } finally { setLoading(false); }
  };

  return (
    <div className="login-wrapper">
      <div className="login-card fade-in">
        <div className="login-logo">🥬</div>
        <div className="login-title">PeriShield AI</div>
        <div className="login-sub" style={{ marginBottom:6 }}>Large-Scale Demand Forecasting</div>
        <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:28,
                      background:'var(--bg-input)', padding:'6px 12px', borderRadius:6,
                      fontFamily:'var(--font-mono)' }}>
          demo: admin / admin123
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input className="form-input" value={username}
              onChange={e => setUsername(e.target.value)} placeholder="admin" />
          </div>
          <div className="form-group" style={{ marginBottom:22 }}>
            <label className="form-label">Password</label>
            <input type="password" className="form-input" value={password}
              onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
          </div>

          {error && <div className="alert alert-error" style={{ marginBottom:16 }}>⚠️ {error}</div>}

          <button type="submit" className="btn btn-primary btn-lg"
            style={{ width:'100%', justifyContent:'center' }} disabled={loading}>
            {loading
              ? <><div className="loading-spinner" style={{ width:18, height:18, borderWidth:2 }} /> Signing in…</>
              : '🚀 Sign In'}
          </button>
        </form>

        <div style={{ marginTop:24, display:'flex', gap:12, justifyContent:'center', flexWrap:'wrap' }}>
          {['RF + LSTM Hybrid','10K+ SKUs','FastAPI','PyTorch'].map(tag => (
            <span key={tag} className="badge badge-blue" style={{ fontSize:10 }}>{tag}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
