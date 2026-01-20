import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { 
  Home, 
  Upload, 
  Database, 
  BarChart3, 
  Trash2, 
  Settings,
  Video,
  LogOut,
  Key
} from 'lucide-react';

import { useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import UploadPage from './pages/UploadPage';
import FilesPage from './pages/FilesPage';
import StatsPage from './pages/StatsPage';
import CachePage from './pages/CachePage';
import AdminPage from './pages/AdminPage';
import SettingsPage from './pages/SettingsPage';
import ApiKeysPage from './pages/ApiKeysPage';

const Navigation = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  
  const navItems = [
    { path: '/admin/', icon: Home, label: 'Dashboard' },
    { path: '/admin/upload', icon: Upload, label: 'Upload' },
    { path: '/admin/files', icon: Database, label: 'Files' },
    { path: '/admin/stats', icon: BarChart3, label: 'Statistics' },
    { path: '/admin/cache', icon: Trash2, label: 'Cache' },
    { path: '/admin/api-keys', icon: Key, label: 'API Keys' },
    { path: '/admin/settings', icon: Settings, label: 'Settings' }
  ];
  
  return (
    <nav style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
    }}>
      <div className="container">
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ 
              background: 'white', 
              padding: '8px', 
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center'
            }}>
              <Video size={24} color="#667eea" />
            </div>
            <div>
              <h1 style={{ color: 'white', fontSize: '24px', fontWeight: 'bold', marginBottom: '2px' }}>
                CDN Control Panel
              </h1>
              <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px', margin: 0 }}>
                Angemeldet als: {user?.username}
              </p>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '10px 16px',
                    background: isActive ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.1)',
                    color: 'white',
                    borderRadius: '6px',
                    textDecoration: 'none',
                    fontSize: '14px',
                    fontWeight: '500',
                    transition: 'all 0.2s',
                    border: isActive ? '2px solid rgba(255,255,255,0.3)' : '2px solid transparent'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = isActive 
                      ? 'rgba(255,255,255,0.2)' 
                      : 'rgba(255,255,255,0.1)';
                  }}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
            
            {/* Logout Button */}
            <button
              onClick={logout}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 16px',
                background: 'rgba(239, 68, 68, 0.9)',
                color: 'white',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s',
                border: 'none',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(220, 38, 38, 1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(239, 68, 68, 0.9)';
              }}
            >
              <LogOut size={18} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Route */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected Routes */}
        <Route path="/admin/*" element={
          <ProtectedRoute>
            <div style={{ minHeight: '100vh', background: '#f5f7fa' }}>
              <Navigation />
              
              <div className="container" style={{ paddingTop: '30px', paddingBottom: '30px' }}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/upload" element={<UploadPage />} />
                  <Route path="/files" element={<FilesPage />} />
                  <Route path="/stats" element={<StatsPage />} />
                  <Route path="/cache" element={<CachePage />} />
                  <Route path="/api-keys" element={<ApiKeysPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </div>
            </div>
          </ProtectedRoute>
        } />
        
        {/* Redirect root to admin */}
        <Route path="/" element={<Navigate to="/admin/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
