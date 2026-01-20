import React, { useState, useEffect } from 'react';
import { Upload as UploadIcon, FileImage, Video, CheckCircle, AlertCircle, LogIn } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { uploadFile } from '../api';

const UploadPage = () => {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [file, setFile] = useState(null);
  const [bucket, setBucket] = useState('media');
  const [folder, setFolder] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSpeed, setUploadSpeed] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [startTime, setStartTime] = useState(null);

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setIsAuthenticated(false);
    } else {
      setIsAuthenticated(true);
    }
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setResult(null);
    setError(null);
    setUploadProgress(0);
    setUploadSpeed(0);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    // Check authentication before upload
    const token = localStorage.getItem('token');
    if (!token) {
      setError('You must be logged in to upload files. Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);
    setUploadProgress(0);
    setUploadSpeed(0);
    const uploadStartTime = Date.now();
    setStartTime(uploadStartTime);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('bucket', bucket);
    formData.append('folder', folder);

    console.log('🚀 Starting upload:', {
      filename: file.name,
      size: (file.size / 1024 / 1024).toFixed(2) + ' MB',
      bucket,
      folder
    });

    try {
      const response = await uploadFile(formData, (percent, loaded, total) => {
        setUploadProgress(percent);
        
        // Calculate upload speed
        const elapsed = (Date.now() - uploadStartTime) / 1000; // seconds
        if (elapsed > 0) {
          const speedMBps = (loaded / 1024 / 1024) / elapsed;
          setUploadSpeed(speedMBps);
        }
      });
      
      console.log('✅ Upload successful:', response.data);
      setResult(response.data);
      setFile(null);
      setUploadProgress(100);
      // Reset file input
      document.getElementById('file-input').value = '';
    } catch (err) {
      console.error('❌ Upload error:', err);
      let errorMsg = 'Upload failed';
      
      if (err.code === 'ECONNABORTED') {
        errorMsg = 'Upload timeout - file may be too large or connection too slow';
      } else if (err.response) {
        console.error('Server response:', err.response);
        if (err.response.status === 401) {
          errorMsg = 'Authentication failed - please login again';
          setTimeout(() => navigate('/login'), 2000);
        } else {
          errorMsg = err.response.data?.detail || `Error: ${err.response.status} ${err.response.statusText}`;
        }
      } else if (err.request) {
        console.error('No response received:', err.request);
        errorMsg = 'No response from server - check your connection';
      } else {
        console.error('Request setup error:', err.message);
        errorMsg = err.message || 'Unknown error occurred';
      }
      
      setError(errorMsg);
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

      {/* Authentication Warning */}
      {!isAuthenticated && (
        <div style={{ 
          marginBottom: '24px', 
          padding: '16px', 
          background: '#fef3c7', 
          borderRadius: '8px',
          border: '1px solid #fbbf24',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <LogIn size={24} color="#d97706" />
          <div>
            <p style={{ color: '#92400e', fontWeight: '600', marginBottom: '4px' }}>
              Authentication Required
            </p>
            <p style={{ color: '#78350f', fontSize: '14px' }}>
              You must be logged in to upload files.{' '}
              <a 
                href="/login" 
                style={{ 
                  color: '#d97706', 
                  textDecoration: 'underline',
                  cursor: 'pointer'
                }}
              >
                Click here to login
              </a>
            </p>
          </div>
        </div>
      )}

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

        {/* Upload Progress */}
        {uploading && (
          <div style={{ marginBottom: '24px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              marginBottom: '8px',
              fontSize: '14px',
              fontWeight: '500'
            }}>
              <span>Uploading... {uploadProgress}%</span>
              <span style={{ color: '#6b7280' }}>
                {uploadSpeed > 0 ? `${uploadSpeed.toFixed(2)} MB/s` : 'Calculating...'}
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              background: '#e5e7eb',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${uploadProgress}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                transition: 'width 0.3s ease',
                borderRadius: '4px'
              }} />
            </div>
            {file && (
              <div style={{ 
                fontSize: '12px', 
                color: '#6b7280', 
                marginTop: '8px',
                textAlign: 'right'
              }}>
                {((file.size / 1024 / 1024) * (uploadProgress / 100)).toFixed(2)} MB / {(file.size / 1024 / 1024).toFixed(2)} MB
              </div>
            )}
          </div>
        )}

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
          {uploading ? `Uploading... ${uploadProgress}%` : 'Upload File'}
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
