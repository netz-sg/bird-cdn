import React, { useState, useEffect } from 'react';
import { Key, Plus, Trash2, Power, Copy, Check, AlertCircle, Calendar, Clock, TestTube } from 'lucide-react';
import { getApiKeys, createApiKey, deleteApiKey, toggleApiKey, testApiKey } from '../api';
import { format } from 'date-fns';

const ApiKeysPage = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: '',
    expires_in_days: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [copiedKey, setCopiedKey] = useState(null);
  const [newApiKey, setNewApiKey] = useState(null);
  const [testingKey, setTestingKey] = useState(null);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      const response = await getApiKeys();
      setApiKeys(response.data.keys);
      setLoading(false);
    } catch (err) {
      setError('Failed to load API keys');
      setLoading(false);
    }
  };

  const handleCreateKey = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!createForm.name) {
      setError('Key name is required');
      return;
    }

    try {
      const payload = {
        name: createForm.name,
        expires_in_days: createForm.expires_in_days ? parseInt(createForm.expires_in_days) : null
      };

      const response = await createApiKey(payload);
      setNewApiKey(response.data.key); // Full key only shown once
      setSuccess('API Key created successfully! Copy it now, it won\'t be shown again.');
      setCreateForm({ name: '', expires_in_days: '' });
      loadApiKeys();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create API key');
    }
  };

  const handleDelete = async (keyId, keyName) => {
    if (!window.confirm(`Delete API key "${keyName}"?`)) return;

    try {
      await deleteApiKey(keyId);
      setSuccess('API key deleted');
      loadApiKeys();
    } catch (err) {
      setError('Failed to delete API key');
    }
  };

  const handleToggle = async (keyId) => {
    try {
      await toggleApiKey(keyId);
      setSuccess('API key status updated');
      loadApiKeys();
    } catch (err) {
      setError('Failed to toggle API key');
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const closeNewKeyModal = () => {
    setNewApiKey(null);
    setShowCreateModal(false);
    setSuccess('');
  };

  const handleTestKey = async (keyValue) => {
    setTestingKey(keyValue);
    setTestResult(null);
    setError('');
    
    try {
      const response = await testApiKey(keyValue);
      setTestResult({
        success: true,
        message: 'API Key works! Successfully authenticated.',
        data: response.data
      });
    } catch (err) {
      setTestResult({
        success: false,
        message: err.response?.status === 401 
          ? 'API Key is invalid or expired' 
          : 'API Key test failed: ' + (err.response?.data?.detail || err.message)
      });
    } finally {
      setTestingKey(null);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '60px' }}>Loading...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '8px' }}>
            API Keys
          </h1>
          <p style={{ color: '#6b7280' }}>
            Manage API keys for external applications and integrations
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 20px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)'
          }}
        >
          <Plus size={18} />
          Create New Key
        </button>
      </div>

      {error && (
        <div style={{
          background: '#fff5f5',
          border: '1px solid #fc8181',
          borderRadius: '8px',
          padding: '12px 16px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: '#c53030'
        }}>
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {success && !newApiKey && (
        <div style={{
          background: '#f0fdf4',
          border: '1px solid #86efac',
          borderRadius: '8px',
          padding: '12px 16px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: '#166534'
        }}>
          <Check size={16} />
          {success}
        </div>
      )}

      {testResult && (
        <div style={{
          background: testResult.success ? '#f0fdf4' : '#fff5f5',
          border: `1px solid ${testResult.success ? '#86efac' : '#fc8181'}`,
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '20px',
          color: testResult.success ? '#166534' : '#c53030'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            {testResult.success ? <Check size={20} /> : <AlertCircle size={20} />}
            <strong>{testResult.success ? '✅ API Key Test Successful' : '❌ API Key Test Failed'}</strong>
          </div>
          <p style={{ margin: 0, fontSize: '14px' }}>{testResult.message}</p>
          {testResult.success && (
            <div style={{ 
              marginTop: '12px', 
              padding: '12px', 
              background: 'rgba(255,255,255,0.5)', 
              borderRadius: '6px',
              fontSize: '13px',
              fontFamily: 'monospace'
            }}>
              <strong>Response:</strong> Fetched {testResult.data?.files?.total || 0} files, {testResult.data?.storage?.used_gb || 0} GB used
            </div>
          )}
          <button
            onClick={() => setTestResult(null)}
            style={{
              marginTop: '12px',
              padding: '6px 12px',
              background: testResult.success ? '#10b981' : '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            Dismiss
          </button>
        </div>
      )}

      {apiKeys.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
          <Key size={48} color="#cbd5e0" style={{ margin: '0 auto 20px' }} />
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
            No API Keys Yet
          </h3>
          <p style={{ color: '#6b7280', marginBottom: '20px' }}>
            Create your first API key to start using the CDN API
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              padding: '10px 20px',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Create API Key
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '16px' }}>
          {apiKeys.map((key) => (
            <div key={key.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{
                      background: key.is_active ? '#10b981' : '#6b7280',
                      padding: '8px',
                      borderRadius: '8px'
                    }}>
                      <Key size={20} color="white" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '4px' }}>
                        {key.name}
                      </h3>
                      <div style={{
                        display: 'inline-block',
                        padding: '4px 12px',
                        background: key.is_active ? '#d1fae5' : '#e5e7eb',
                        color: key.is_active ? '#065f46' : '#374151',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '600'
                      }}>
                        {key.is_active ? 'Active' : 'Inactive'}
                      </div>
                    </div>
                  </div>

                  <div style={{
                    background: '#f9fafb',
                    padding: '12px',
                    borderRadius: '6px',
                    marginBottom: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontFamily: 'monospace',
                    fontSize: '13px'
                  }}>
                    <code style={{ color: '#374151' }}>{key.key}</code>
                    <button
                      onClick={() => copyToClipboard(key.key, key.id)}
                      style={{
                        background: copiedKey === key.id ? '#10b981' : '#667eea',
                        color: 'white',
                        border: 'none',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '12px'
                      }}
                    >
                      {copiedKey === key.id ? <Check size={14} /> : <Copy size={14} />}
                      {copiedKey === key.id ? 'Copied!' : 'Copy'}
                    </button>
                  </div>

                  <div style={{ display: 'flex', gap: '20px', fontSize: '13px', color: '#6b7280' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Calendar size={14} />
                      Created: {key.created_at ? format(new Date(key.created_at), 'MMM dd, yyyy') : 'N/A'}
                    </div>
                    {key.expires_at && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444' }}>
                        <Clock size={14} />
                        Expires: {format(new Date(key.expires_at), 'MMM dd, yyyy')}
                      </div>
                    )}
                    {key.last_used_at && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Clock size={14} />
                        Last used: {format(new Date(key.last_used_at), 'MMM dd, yyyy HH:mm')}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => handleTestKey(key.key)}
                    disabled={testingKey === key.key}
                    style={{
                      padding: '8px',
                      background: testingKey === key.key ? '#e5e7eb' : '#dbeafe',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: testingKey === key.key ? 'not-allowed' : 'pointer',
                      color: '#1e40af'
                    }}
                    title="Test API Key"
                  >
                    <TestTube size={16} />
                  </button>
                  <button
                    onClick={() => handleToggle(key.id)}
                    style={{
                      padding: '8px',
                      background: key.is_active ? '#fef3c7' : '#d1fae5',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      color: key.is_active ? '#92400e' : '#065f46'
                    }}
                    title={key.is_active ? 'Deactivate' : 'Activate'}
                  >
                    <Power size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(key.id, key.name)}
                    style={{
                      padding: '8px',
                      background: '#fee2e2',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      color: '#991b1b'
                    }}
                    title="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            maxWidth: '500px',
            width: '100%',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
            margin: '20px'
          }}>
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid #e5e7eb'
            }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', margin: 0 }}>
                Create New API Key
              </h2>
            </div>

            <form onSubmit={handleCreateKey} style={{ padding: '24px' }}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '8px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151'
                }}>
                  Key Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g., PayloadCMS Production"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '2px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                  required
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '8px',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151'
                }}>
                  Expires In (Days)
                </label>
                <input
                  type="number"
                  placeholder="Leave empty for no expiration"
                  value={createForm.expires_in_days}
                  onChange={(e) => setCreateForm({ ...createForm, expires_in_days: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '2px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                  min="1"
                />
                <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '6px' }}>
                  Optional: Set an expiration date for the key
                </p>
              </div>

              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setCreateForm({ name: '', expires_in_days: '' });
                    setError('');
                  }}
                  style={{
                    padding: '10px 20px',
                    background: '#e5e7eb',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    padding: '10px 20px',
                    background: '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Create Key
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Key Display Modal */}
      {newApiKey && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1001
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            maxWidth: '600px',
            width: '100%',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
            margin: '20px'
          }}>
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid #e5e7eb',
              background: '#10b981',
              color: 'white',
              borderTopLeftRadius: '12px',
              borderTopRightRadius: '12px'
            }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Check size={24} />
                API Key Created Successfully!
              </h2>
            </div>

            <div style={{ padding: '24px' }}>
              <div style={{
                background: '#fef3c7',
                border: '2px solid #fbbf24',
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '20px'
              }}>
                <p style={{ fontSize: '14px', color: '#92400e', margin: 0, fontWeight: '600' }}>
                  ⚠️ Important: Copy this key now! It won't be shown again.
                </p>
              </div>

              <div style={{
                background: '#1f2937',
                padding: '16px',
                borderRadius: '8px',
                marginBottom: '20px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <code style={{
                    color: '#10b981',
                    fontFamily: 'monospace',
                    fontSize: '13px',
                    wordBreak: 'break-all'
                  }}>
                    {newApiKey}
                  </code>
                  <button
                    onClick={() => copyToClipboard(newApiKey, 'new')}
                    style={{
                      background: '#10b981',
                      color: 'white',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      marginLeft: '12px',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {copiedKey === 'new' ? <Check size={14} /> : <Copy size={14} />}
                    {copiedKey === 'new' ? 'Copied!' : 'Copy'}
                  </button>
                </div>
              </div>

              <button
                onClick={closeNewKeyModal}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                I've Copied the Key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApiKeysPage;
