
// // src/App.js
// import React from 'react';
// import { BrowserRouter as Router, Route, Routes, Navigate} from 'react-router-dom';
// import Login from './components/Login';
// import Dashboard from './components/Dashboards';

// function App() {

//   const isAuthenticated = sessionStorage.getItem('authToken') !== null;
//   console.log('isAuthenticated:',isAuthenticated);
//   return (
//     <Router>
//       <Routes>
//         <Route path="/" element={<Navigate to="/login" replace />} />
//         <Route path="/login" element={<Login />} />
//         {/* <Route path="/dashboard" element={<Dashboard />} /> */}
//         <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" replace />}/>
//       </Routes>
//     </Router>
//   );
// }

// export default App;



import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboards';
import AdminDashboard from './components/Admin';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = sessionStorage.getItem('authToken');
    setIsAuthenticated(token !== null);
  }, []);

  return (
    <Router>
      <Routes>
      <Route path="/admin" element={<AdminDashboard />} />

        {/* Redirect root path to login */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Login page */}
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login onLogin={() => setIsAuthenticated(true)} />
          }
        />

        {/* Dashboard page */}
        <Route
          path="/dashboard"
          element={
            isAuthenticated ? (
              <Dashboard onLogout={() => setIsAuthenticated(false)} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
