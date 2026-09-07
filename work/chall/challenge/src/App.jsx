import { useState } from 'react';
import { motion } from 'framer-motion';

export default function App() {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState('Ready');
  const [savedId, setSavedId] = useState('');
  const [previewHtml, setPreviewHtml] = useState('');

  const handleSave = async () => {
    if (!title || !content) {
      setStatus('Please enter both title and content.');
      return;
    }
    setStatus('Saving draft...');

    try {
      const response = await fetch('/api/draft/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to save');

      setSavedId(data.id);
      setStatus(`Saved successfully! Draft ID: ${data.id}`);
    } catch (error) {
      setStatus(error.message);
    }
  };

  const handlePreview = async () => {
    if (!title && !content) {
      setStatus('Write something before previewing.');
      return;
    }
    setStatus('Generating live preview...');

    try {
      const payload = {
        title: title || 'Untitled Draft',
        content: content || '',
      };

      const response = await fetch('/api/draft/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: JSON.stringify(payload) }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Preview failed');

      setPreviewHtml(data.preview || '');
      setStatus('Preview generated.');
    } catch (error) {
      setStatus(error.message);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0b0f19', color: '#f3f4f6', fontFamily: 'Inter, system-ui, sans-serif', padding: '40px 20px' }}>
      <div style={{ maxWidth: 860, margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          style={{
            background: 'rgba(17, 24, 39, 0.8)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 20,
            padding: 36,
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          }}
        >
          <header style={{ marginBottom: 28 }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 700, margin: 0, background: 'linear-gradient(135deg, #6366f1, #a855f7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Draft Sync Studio
            </h1>
            <p style={{ color: '#9ca3af', marginTop: 6, fontSize: '0.95rem' }}>
              Collaborative workspace with real-time draft synchronization.
            </p>
          </header>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ display: 'block', marginBottom: 6, fontSize: '0.875rem', fontWeight: 600, color: '#d1d5db' }}>Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter draft title..."
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: 10,
                  border: '1px solid #374151',
                  background: '#1f2937',
                  color: '#ffffff',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: 6, fontSize: '0.875rem', fontWeight: 600, color: '#d1d5db' }}>Content</label>
              <textarea
                rows={7}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write markdown or draft text here..."
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: 10,
                  border: '1px solid #374151',
                  background: '#1f2937',
                  color: '#ffffff',
                  outline: 'none',
                  resize: 'vertical',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              <button
                onClick={handleSave}
                style={{
                  padding: '12px 24px',
                  borderRadius: 10,
                  border: 'none',
                  background: 'linear-gradient(135deg, #4f46e5, #6366f1)',
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                Save Draft
              </button>
              <button
                onClick={handlePreview}
                style={{
                  padding: '12px 24px',
                  borderRadius: 10,
                  border: '1px solid #4b5563',
                  background: '#374151',
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                Live Preview
              </button>
            </div>

            {status && (
              <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 8, background: '#111827', border: '1px solid #1f2937', color: '#9ca3af', fontSize: '0.875rem' }}>
                Status: <span style={{ color: '#e5e7eb' }}>{status}</span>
              </div>
            )}
          </div>

          {previewHtml && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              style={{
                marginTop: 28,
                padding: 20,
                borderRadius: 12,
                background: '#1f2937',
                border: '1px solid #374151',
              }}
            >
              <h3 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#818cf8' }}>Rendered Preview</h3>
              <div
                style={{ color: '#e5e7eb', lineHeight: 1.6 }}
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
