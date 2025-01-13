import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

import './Login.css';


function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const apiUrl = process.env.REACT_APP_API_URL;
  

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${apiUrl}/api/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      }); 

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      
      // Ensure these keys match the keys in your backend response
      sessionStorage.setItem('authToken', data.access);  
      sessionStorage.setItem('refreshToken', data.refresh); 
      sessionStorage.setItem('userName', data.username);
      onLogin();
      // Navigate to the dashboard
      if (data.username === 'admin') {
        navigate('/admin');
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      setError('Invalid credentials');
      console.error('Error during login:', error);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <h2 className="login-title">Login</h2>
        {error && <p className="error-message">{error}</p>}
        <form className="login-form" onSubmit={handleLogin}>
          <input
            className="input-field"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Username"
            required
          />
          <input
            className="input-field"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
          />
          <button className="submit-btn" type="submit">Login</button>
        </form>
      </div>
    </div>
  );
}

export default Login;

