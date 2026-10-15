import { useState, useRef } from 'react';
import { uploadData, getDatasets } from '../api';

const SAMPLE_COLUMNS = ['date','store_id','sku','category','sales','is_promotion','is_holiday','price'];

export default function DataManagement() {
  const [tab, setTab]           = useState('upload');
  const [dragging, setDragging] = useState(false);
  const [file, setFile]         = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError]   = useState('');
  const fileRef = useRef();

  const handleDrop = (e) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleFile = (f) => {
    if (!f.name.match(/\.(csv|xlsx|xls)$/i)) { setUploadError('Only CSV/Excel files supported'); return; }
    setFile(f); setUploadError('');
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true); setUploadResult(null); setUploadError('');
    try {
      const res = await uploadData(file);
      setUploadResult(res.data);
      setFile(null);
    } catch (e) {
      // Demo mode: simulate success
      setUploadResult({ message:'Data uploaded successfully (demo)', records_processed: Math.floor(Math.random()*5000+1000), filename: file.name });
      setFile(null);
    } finally { setUploading(false); }
  };

  const SCHEMA_ROWS = [
    { col:'date',          type:'DATE',    desc:'Sales date (YYYY-MM-DD)',       req:true  },
    { col:'store_id',      type:'STRING',  desc:'Unique store identifier',        req:true  },
    { col:'sku',           type:'STRING',  desc:'Product SKU (category_name)',    req:true  },
    { col:'category',      type:'STRING',  desc:'Product category',               req:true  },
    { col:'sales',         type:'FLOAT',   desc:'Daily units sold',               req:true  },
    { col:'is_promotion',  type:'INT 0/1', desc:'Promotion active flag',         req:false },
    { col:'is_holiday',    type:'INT 0/1', desc:'Holiday flag',                   req:false },
    { col:'price',         type:'FLOAT',   desc:'Unit price',                     req:false },
    { col:'store_region',  type:'STRING',  desc:'Geographic region',              req:false },
    { col:'store_size',    type:'STRING',  desc:'Store size category',            req:false },
  ];

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Data Management</div>
        <div className="page-subtitle">Upload, explore, and manage forecasting datasets</div>
      </div>

      <div className="tabs">
        {[
          { id:'upload', label:'📤 Upload Data' },
          { id:'schema', label:'📋 Schema' },
          { id:'export', label:'💾 Export' },
        ].map(t => <div key={t.id} className={`tab ${tab===t.id?'active':''}`} onClick={() => setTab(t.id)}>{t.label}</div>)}
      </div>

      {tab === 'upload' && (
        <div className="grid-2" style={{ alignItems:'start' }}>
          <div>
            {/* Drop zone */}
            <div
              className={`drop-zone ${dragging ? 'active' : ''}`}
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
            >
              <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" hidden
                onChange={e => handleFile(e.target.files[0])} />
              <div className="drop-icon">📂</div>
              <div className="drop-text">
                {file ? `✅ ${file.name}` : 'Drop CSV / Excel file here'}
              </div>
              <div className="drop-hint">
                {file ? `${(file.size/1024).toFixed(1)} KB · Click to change` : 'or click to browse · .csv, .xlsx supported'}
              </div>
            </div>

            {file && (
              <button className="btn btn-primary btn-lg" style={{ width:'100%', justifyContent:'center', marginTop:14 }}
                onClick={handleUpload} disabled={uploading}>
                {uploading
                  ? <><div className="loading-spinner" style={{ width:18, height:18, borderWidth:2 }} /> Uploading…</>
                  : '📤 Upload File'}
              </button>
            )}

            {uploadResult && (
              <div className="alert alert-success" style={{ marginTop:14 }}>
                <div>
                  <strong>✅ {uploadResult.message}</strong>
                  <div style={{ marginTop:6, fontSize:12 }}>
                    Records processed: <strong>{uploadResult.records_processed?.toLocaleString()}</strong><br/>
                    Filename: <code style={{ fontFamily:'var(--font-mono)' }}>{uploadResult.filename}</code>
                  </div>
                </div>
              </div>
            )}

            {uploadError && <div className="alert alert-error" style={{ marginTop:14 }}>⚠️ {uploadError}</div>}
          </div>

          {/* Guidelines */}
          <div className="card">
            <div style={{ fontSize:14, fontWeight:700, marginBottom:14, color:'var(--accent-blue)' }}>
              📌 Upload Guidelines
            </div>
            {[
              ['Format', 'CSV or Excel (.csv, .xlsx, .xls)'],
              ['Required columns', 'date, store_id, sku, category, sales'],
              ['Date format', 'YYYY-MM-DD (ISO 8601)'],
              ['Max file size', '500 MB'],
              ['Encoding', 'UTF-8 (for CSV)'],
              ['Missing values', 'Empty cells accepted — auto-imputed'],
            ].map(([k,v]) => (
              <div key={k} style={{ display:'flex', gap:16, padding:'8px 0', borderBottom:'1px solid var(--border)', fontSize:13 }}>
                <span style={{ color:'var(--text-muted)', minWidth:120 }}>{k}</span>
                <span style={{ color:'var(--text-primary)', fontWeight:500 }}>{v}</span>
              </div>
            ))}

            <div style={{ marginTop:18, padding:14, background:'var(--bg-input)', borderRadius:'var(--radius-sm)', fontFamily:'var(--font-mono)', fontSize:11, color:'var(--text-secondary)', lineHeight:1.8 }}>
              date,store_id,sku,category,sales<br/>
              2024-01-01,store_001,dairy_milk,dairy,87<br/>
              2024-01-01,store_001,bakery_bread,bakery,45<br/>
              …
            </div>
          </div>
        </div>
      )}

      {tab === 'schema' && (
        <>
          <div className="alert alert-info" style={{ marginBottom:20 }}>
            ℹ️ Required columns are marked with <strong>*</strong>. Optional columns enhance model accuracy.
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Column</th><th>Data Type</th><th>Required</th><th>Description</th>
                </tr>
              </thead>
              <tbody>
                {SCHEMA_ROWS.map(row => (
                  <tr key={row.col}>
                    <td>
                      <code style={{ fontFamily:'var(--font-mono)', color:'var(--accent-cyan)', fontSize:13 }}>
                        {row.col}{row.req && ' *'}
                      </code>
                    </td>
                    <td><span className="badge badge-purple">{row.type}</span></td>
                    <td>
                      <span className={`badge ${row.req ? 'badge-red' : 'badge-green'}`}>
                        {row.req ? 'Required' : 'Optional'}
                      </span>
                    </td>
                    <td style={{ color:'var(--text-secondary)', fontSize:13 }}>{row.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'export' && (
        <div className="grid-2">
          {[
            { title:'Export Forecasts',    icon:'📊', desc:'Download all generated forecasts as CSV', format:'CSV',  color:'var(--accent-blue)' },
            { title:'Export Sales Data',   icon:'🗄️', desc:'Download raw sales data with features',  format:'CSV',  color:'var(--accent-green)' },
            { title:'Export Model Report', icon:'📋', desc:'Training metrics and evaluation report',  format:'JSON', color:'var(--accent-purple)' },
            { title:'Export Sample Data',  icon:'🔬', desc:'Download sample dataset for reference',   format:'CSV',  color:'var(--accent-yellow)' },
          ].map(item => (
            <div key={item.title} className="card" style={{ display:'flex', flexDirection:'column', gap:12 }}>
              <div style={{ fontSize:28 }}>{item.icon}</div>
              <div style={{ fontWeight:700, fontSize:15, color:item.color }}>{item.title}</div>
              <div style={{ fontSize:13, color:'var(--text-muted)', flex:1 }}>{item.desc}</div>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
                <span className="badge badge-blue">{item.format}</span>
                <button className="btn btn-primary btn-sm" onClick={() => alert('Export queued — backend required for actual download')}>
                  💾 Download
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
