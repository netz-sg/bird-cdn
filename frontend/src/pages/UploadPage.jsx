import React, { useState } from 'react';
import { Upload as UploadIcon, FileImage, Video, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadFile } from '../api';

const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [bucket, setBucket] = useState('media');
  const [folder, setFolder] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setResult(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('bucket', bucket);
    formData.append('folder', folder);

    try {
      const response = await uploadFile(formData);
      setResult(response.data);
      setFile(null);
      // Reset file input
      document.getElementById('file-input').value = '';
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = () => {
    if (!file) return <FileImage size={48} color="#9ca3af" />;
    
    const type = file.type.split('/')[0];
    if (type === 'image') return <FileImage size={48} color="#3b82f6" />;
    if (type === 'video') return <Video size={48} color="#8b5cf6" />;
    return <FileImage size={48} color="#9ca3af" />;
  };

  return (
    <div>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '8px' }}>
          Upload Files
        </h1>
        <p style={{ color: '#6b7280' }}>
          Upload images and videos to your CDN
        </p>
      </div>

      <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* File Selector */}
        <div style={{ 
          border: '2px dashed #d1d5db', 
          borderRadius: '12px', 
          padding: '60px 40px',
          textAlign: 'center',
          background: '#f9fafb',
          marginBottom: '24px'
        }}>
          {getFileIcon()}
          
          <div style={{ marginTop: '20px' }}>
            <label htmlFor="file-input" className="btn btn-primary" style={{ cursor: 'pointer' }}>
              <UploadIcon size={18} />
              Select File
            </label>
            <input
              id="file-input"
              type="file"
              onChange={handleFileChange}
              accept="image/*,video/*"
              style={{ display: 'none' }}
            />
          </div>

          {file && (
            <div style={{ marginTop: '16px' }}>
              <p style={{ fontWeight: '500', color: '#1f2937' }}>{file.name}</p>
              <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '4px' }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          )}
        </div>

        {/* Upload Options */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Bucket
            </label>
            <input
              type="text"
              value={bucket}
              onChange={(e) => setBucket(e.target.value)}
              placeholder="media"
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Folder (optional)
            </label>
            <input
              type="text"
              value={folder}
              onChange={(e) => setFolder(e.target.value)}
              placeholder="e.g., images/2024"
            />
          </div>
        </div>

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="btn btn-primary"
          style={{ 
            width: '100%', 
            justifyContent: 'center',
            opacity: (!file || uploading) ? 0.5 : 1,
            cursor: (!file || uploading) ? 'not-allowed' : 'pointer'
          }}
        >
          {uploading ? 'Uploading...' : 'Upload File'}
        </button>

        {/* Success Message */}
        {result && (
          <div style={{ 
            marginTop: '24px', 
            padding: '16px', 
            background: '#d1fae5', 
            borderRadius: '8px',
            border: '1px solid #6ee7b7'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
              <CheckCircle size={24} color="#059669" />
              <h4 style={{ fontSize: '16px', fontWeight: '600', color: '#065f46' }}>
                Upload Successful!
              </h4>
            </div>
            
            <div style={{ fontSize: '14px', color: '#047857' }}>
              <p style={{ marginBottom: '8px' }}>
                <strong>File:</strong> {result.filename}
              </p>
              <p style={{ marginBottom: '8px' }}>
                <strong>CDN URL:</strong>
              </p>
              <input
                type="text"
                value={result.cdn_url}
                readOnly
                onClick={(e) => e.target.select()}
                style={{ 
                  marginBottom: '8px',
                  fontFamily: 'monospace',
                  fontSize: '12px'
                }}
              />
              <button
                onClick={() => {
                  navigator.clipboard.writeText(result.cdn_url);
                  alert('URL copied to clipboard!');
                }}
                className="btn"
                style={{ 
                  background: '#10b981', 
                  color: 'white',
                  fontSize: '12px',
                  padding: '6px 12px'
                }}
              >
                Copy URL
              </button>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div style={{ 
            marginTop: '24px', 
            padding: '16px', 
            background: '#fee2e2', 
            borderRadius: '8px',
            border: '1px solid #fca5a5',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <AlertCircle size={24} color="#dc2626" />
            <p style={{ color: '#991b1b', fontWeight: '500' }}>{error}</p>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="card" style={{ maxWidth: '800px', margin: '24px auto 0', background: '#eff6ff' }}>
        <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', color: '#1e40af' }}>
          ℹ️ Upload Information
        </h4>
        <ul style={{ fontSize: '14px', color: '#1e3a8a', lineHeight: '1.8', paddingLeft: '20px' }}>
          <li>Max file size: 5 GB</li>
          <li>Supported images: JPG, PNG, GIF, WebP, SVG</li>
          <li>Supported videos: MP4, WebM, AVI, MOV, MKV</li>
          <li>Files are automatically cached after first request</li>
        </ul>
      </div>
    </div>
  );
};

export default UploadPage;
