import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  HardDrive, 
  Zap, 
  Activity,
  Database,
  AlertTriangle,
  X,
  Check,
  Lock,
  User as UserIcon,
  BarChart2,
  Server,
  ExternalLink
} from 'lucide-react';
import { getOverview, getBandwidth, changePassword, changeUsername } from '../api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';
import { useAuth } from '../context/AuthContext';

const StatCard = ({ icon: Icon, title, value, subtitle, color }) => (
  <div className="card" style={{ 
    background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
    border: `1px solid ${color}30`
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '8px' }}>{title}</p>
        <h2 style={{ fontSize: '32px', fontWeight: 'bold', color: color, marginBottom: '4px' }}>
          {value}
        </h2>
        {subtitle && <p style={{ color: '#9ca3af', fontSize: '12px' }}>{subtitle}</p>}
      </div>
      <div style={{ 
        background: color, 
        padding: '12px', 
        borderRadius: '12px',
        boxShadow: `0 4px 12px ${color}40`
      }}>
        <Icon size={24} color="white" />
      </div>
    </div>
  </div>
);

const Dashboard = () => {
  const { user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [bandwidth, setBandwidth] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showSecurityModal, setShowSecurityModal] = useState(false);
  const [securityForm, setSecurityForm] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
    newUsername: '',
    usernamePassword: ''
  });
  const [securityError, setSecurityError] = useState('');
  const [securitySuccess, setSecuritySuccess] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [changingUsername, setChangingUsername] = useState(false);

  const isDefaultCredentials = user?.username === 'admin';

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [overviewRes, bandwidthRes] = await Promise.all([
        getOverview(),
        getBandwidth(7)
      ]);
      
      setOverview(overviewRes.data);
      setBandwidth(bandwidthRes.data.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setLoading(false);
    }
  };

  const handlePasswordChange = async () => {
    setSecurityError('');
    setSecuritySuccess('');

    if (securityForm.newPassword !== securityForm.confirmPassword) {
      setSecurityError('Neue Passwörter stimmen nicht überein');
      return;
    }

    if (securityForm.newPassword.length < 8) {
      setSecurityError('Passwort muss mindestens 8 Zeichen lang sein');
      return;
    }

    setChangingPassword(true);
    try {
      await changePassword(securityForm.oldPassword, securityForm.newPassword);
      setSecuritySuccess('Passwort erfolgreich geändert!');
      setSecurityForm({ ...securityForm, oldPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      setSecurityError(error.response?.data?.detail || 'Fehler beim Ändern des Passworts');
    } finally {
      setChangingPassword(false);
    }
  };

  const handleUsernameChange = async () => {
    setSecurityError('');
    setSecuritySuccess('');

    if (!securityForm.newUsername || securityForm.newUsername.length < 3) {
      setSecurityError('Benutzername muss mindestens 3 Zeichen lang sein');
      return;
    }

    if (securityForm.newUsername === 'admin') {
      setSecurityError('Benutzername "admin" ist nicht erlaubt');
      return;
    }

    setChangingUsername(true);
    try {
      const response = await changeUsername(securityForm.newUsername, securityForm.usernamePassword);
      setSecuritySuccess('Benutzername erfolgreich geändert!');
      
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      setSecurityForm({ ...securityForm, newUsername: '', usernamePassword: '' });
      
      // Page will reload to update navigation after modal is closed
    } catch (error) {
      setSecurityError(error.response?.data?.detail || 'Fehler beim Ändern des Benutzernamens');
    } finally {
      setChangingUsername(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <Activity size={48} color="#3b82f6" style={{ animation: 'spin 1s linear infinite' }} />
        <p style={{ marginTop: '20px', color: '#6b7280' }}>Loading dashboard...</p>
      </div>
    );
  }

  if (!overview) {
    return <div>Error loading data</div>;
  }

  return (
    <div>
      {isDefaultCredentials && (
        <div style={{
          background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
          color: 'white',
          padding: '16px 20px',
          borderRadius: '12px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 12px rgba(245, 158, 11, 0.3)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <AlertTriangle size={24} />
            <div>
              <strong style={{ display: 'block', marginBottom: '4px' }}>
                ⚠️ Sicherheitswarnung: Standard-Zugangsdaten aktiv!
              </strong>
              <span style={{ fontSize: '14px', opacity: 0.9 }}>
                Bitte ändern Sie sofort Ihren Benutzernamen und Passwort.
              </span>
            </div>
          </div>
          <button
            onClick={() => setShowSecurityModal(true)}
            style={{
              background: 'white',
              color: '#d97706',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '8px',
              fontWeight: '600',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
          >
            Jetzt ändern
          </button>
        </div>
      )}

      {showSecurityModal && (
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
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            maxWidth: '500px',
            width: '100%',
            maxHeight: '90vh',
            overflow: 'auto',
            boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
          }}>
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid #e5e7eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', margin: 0 }}>
                🔐 Sicherheitseinstellungen
              </h2>
              <button
                onClick={() => setShowSecurityModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px',
                  color: '#6b7280'
                }}
              >
                <X size={24} />
              </button>
            </div>

            <div style={{ padding: '24px' }}>
              {securityError && (
                <div style={{
                  background: '#fff5f5',
                  border: '1px solid #fc8181',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  marginBottom: '16px',
                  color: '#c53030',
                  fontSize: '14px'
                }}>
                  {securityError}
                </div>
              )}

              {securitySuccess && (
                <div style={{
                  background: '#f0fdf4',
                  border: '1px solid #86efac',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  marginBottom: '16px',
                  color: '#166534',
                  fontSize: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <Check size={16} />
                  {securitySuccess}
                </div>
              )}

              <div style={{
                marginBottom: '24px',
                padding: '16px',
                background: '#f9fafb',
                borderRadius: '8px',
                border: '1px solid #e5e7eb'
              }}>
                <h3 style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  marginBottom: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <UserIcon size={18} />
                  Benutzername ändern
                </h3>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '6px',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#374151'
                  }}>
                    Neuer Benutzername
                  </label>
                  <input
                    type="text"
                    placeholder="Neuer Benutzername"
                    value={securityForm.newUsername}
                    onChange={(e) => setSecurityForm({ ...securityForm, newUsername: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '6px',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#374151'
                  }}>
                    Aktuelles Passwort bestätigen
                  </label>
                  <input
                    type="password"
                    placeholder="Aktuelles Passwort"
                    value={securityForm.usernamePassword}
                    onChange={(e) => setSecurityForm({ ...securityForm, usernamePassword: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <button
                  onClick={handleUsernameChange}
                  disabled={changingUsername || !securityForm.newUsername || !securityForm.usernamePassword}
                  style={{
                    width: '100%',
                    padding: '10px 16px',
                    background: changingUsername || !securityForm.newUsername || !securityForm.usernamePassword ? '#d1d5db' : '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: changingUsername || !securityForm.newUsername || !securityForm.usernamePassword ? 'not-allowed' : 'pointer'
                  }}
                >
                  {changingUsername ? 'Wird geändert...' : 'Benutzername ändern'}
                </button>
              </div>

              <div style={{
                padding: '16px',
                background: '#f9fafb',
                borderRadius: '8px',
                border: '1px solid #e5e7eb'
              }}>
                <h3 style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  marginBottom: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <Lock size={18} />
                  Passwort ändern
                </h3>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '6px',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#374151'
                  }}>
                    Altes Passwort
                  </label>
                  <input
                    type="password"
                    placeholder="Altes Passwort"
                    value={securityForm.oldPassword}
                    onChange={(e) => setSecurityForm({ ...securityForm, oldPassword: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '6px',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#374151'
                  }}>
                    Neues Passwort
                  </label>
                  <input
                    type="password"
                    placeholder="Mindestens 8 Zeichen"
                    value={securityForm.newPassword}
                    onChange={(e) => setSecurityForm({ ...securityForm, newPassword: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{
                    display: 'block',
                    marginBottom: '6px',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#374151'
                  }}>
                    Neues Passwort bestätigen
                  </label>
                  <input
                    type="password"
                    placeholder="Passwort wiederholen"
                    value={securityForm.confirmPassword}
                    onChange={(e) => setSecurityForm({ ...securityForm, confirmPassword: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <button
                  onClick={handlePasswordChange}
                  disabled={changingPassword || !securityForm.oldPassword || !securityForm.newPassword}
                  style={{
                    width: '100%',
                    padding: '10px 16px',
                    background: changingPassword || !securityForm.oldPassword || !securityForm.newPassword ? '#d1d5db' : '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: changingPassword || !securityForm.oldPassword || !securityForm.newPassword ? 'not-allowed' : 'pointer'
                  }}
                >
                  {changingPassword ? 'Wird geändert...' : 'Passwort ändern'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '8px' }}>
          Dashboard
        </h1>
        <p style={{ color: '#6b7280' }}>
          Overview of your CDN performance and statistics
        </p>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <StatCard
          icon={Database}
          title="Total Files"
          value={overview.files.total.toLocaleString()}
          subtitle={`${overview.files.images} images, ${overview.files.videos} videos`}
          color="#3b82f6"
        />
        
        <StatCard
          icon={HardDrive}
          title="Storage Used"
          value={`${overview.storage.used_gb} GB`}
          subtitle={`${(overview.storage.used_bytes / 1024 / 1024).toFixed(0)} MB total`}
          color="#10b981"
        />
        
        <StatCard
          icon={Zap}
          title="Cache Hit Ratio"
          value={`${overview.cache.hit_ratio}%`}
          subtitle={`${overview.cache.cached_files} files cached`}
          color="#f59e0b"
        />
        
        <StatCard
          icon={TrendingUp}
          title="Bandwidth (24h)"
          value={`${overview.bandwidth.last_24h_gb} GB`}
          subtitle="Last 24 hours"
          color="#8b5cf6"
        />
      </div>

      <div className="card">
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>
          Bandwidth Usage (Last 7 Days)
        </h3>
        
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={bandwidth}>
            <defs>
              <linearGradient id="colorBandwidth" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="hour" 
              tickFormatter={(value) => format(new Date(value), 'MMM dd')}
              stroke="#6b7280"
            />
            <YAxis stroke="#6b7280" />
            <Tooltip 
              labelFormatter={(value) => format(new Date(value), 'MMM dd, HH:mm')}
              formatter={(value) => [`${value.toFixed(2)} GB`, 'Bandwidth']}
            />
            <Area 
              type="monotone" 
              dataKey="gb_sent" 
              stroke="#3b82f6" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorBandwidth)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="card" style={{ marginTop: '20px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
          Quick Actions
        </h3>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <a href="/admin/upload" className="btn btn-primary">
            Upload Files
          </a>
          <a href="/admin/cache" className="btn btn-danger">
            Purge Cache
          </a>
          <a href="/admin/stats" className="btn btn-success">
            View Analytics
          </a>
        </div>
      </div>

      <div className="card" style={{ marginTop: '20px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
          🔧 System Tools
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px',
              background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
              color: 'white',
              borderRadius: '10px',
              textDecoration: 'none',
              transition: 'all 0.2s',
              boxShadow: '0 2px 8px rgba(249, 115, 22, 0.3)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(249, 115, 22, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(249, 115, 22, 0.3)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <BarChart2 size={20} />
              <div>
                <div style={{ fontWeight: '600', fontSize: '15px' }}>Grafana</div>
                <div style={{ fontSize: '12px', opacity: 0.9 }}>Dashboards</div>
              </div>
            </div>
            <ExternalLink size={16} />
          </a>

          <a
            href="http://localhost:9090"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px',
              background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
              color: 'white',
              borderRadius: '10px',
              textDecoration: 'none',
              transition: 'all 0.2s',
              boxShadow: '0 2px 8px rgba(239, 68, 68, 0.3)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(239, 68, 68, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(239, 68, 68, 0.3)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Activity size={20} />
              <div>
                <div style={{ fontWeight: '600', fontSize: '15px' }}>Prometheus</div>
                <div style={{ fontSize: '12px', opacity: 0.9 }}>Metrics</div>
              </div>
            </div>
            <ExternalLink size={16} />
          </a>

          <a
            href="http://localhost:9011"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px',
              background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
              color: 'white',
              borderRadius: '10px',
              textDecoration: 'none',
              transition: 'all 0.2s',
              boxShadow: '0 2px 8px rgba(139, 92, 246, 0.3)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(139, 92, 246, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(139, 92, 246, 0.3)';
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Server size={20} />
              <div>
                <div style={{ fontWeight: '600', fontSize: '15px' }}>MinIO</div>
                <div style={{ fontSize: '12px', opacity: 0.9 }}>Storage Console</div>
              </div>
            </div>
            <ExternalLink size={16} />
          </a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
