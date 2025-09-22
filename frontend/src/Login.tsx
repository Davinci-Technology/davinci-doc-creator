import React from 'react';
import './App.css';

const Login: React.FC = () => {
  const handleLogin = () => {
    // Redirect to Azure AD login
    window.location.href = '/api/auth/login';
  };

  return (
    <div className="App">
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)'
      }}>
        <div style={{
          backgroundColor: 'white',
          padding: '3rem',
          borderRadius: '10px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
          textAlign: 'center',
          maxWidth: '400px',
          width: '90%'
        }}>
          <h1 style={{
            color: '#333',
            marginBottom: '1.5rem',
            fontSize: '2rem'
          }}>
            Davinci Document Creator
          </h1>

          <p style={{
            color: '#666',
            marginBottom: '2rem',
            fontSize: '1.1rem'
          }}>
            Convert your Markdown documents to beautifully formatted PDFs
          </p>

          <button
            onClick={handleLogin}
            style={{
              backgroundColor: '#0078d4',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              fontSize: '16px',
              borderRadius: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              margin: '0 auto',
              transition: 'background-color 0.3s ease'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = '#106ebe';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = '#0078d4';
            }}
          >
            <svg
              width="21"
              height="21"
              viewBox="0 0 21 21"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
              <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
              <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
              <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
            </svg>
            Sign in with Microsoft
          </button>

          <p style={{
            marginTop: '2rem',
            fontSize: '0.9rem',
            color: '#999'
          }}>
            Use your Davinci AI Solutions account to access this application
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;