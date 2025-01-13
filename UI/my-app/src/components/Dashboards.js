// src/Dashboard.js
import React from 'react';

import { useState } from 'react';
import './App.css';
import LeftSidebar from './LeftSidebar';
import MainContent from './MainContent';
import ThemeProvider from './main_sub_components/ThemeProvider'; // Import ThemeProvider

function Dashboard({ onLogout}) {

  const [history, setHistory] = useState({ today: [], yesterday: [], last_week: [], last_month: [] });
  const [selectedSessionId, setSelectedSessionId] = useState(null); // Store the selected session ID
  const [selectedFiles, setSelectedFiles] = useState([]); // Store selected files
  const [selectedFolderPath, setSelectedFolderPath] = useState(""); 

  // Callback function to handle history clicks
  const handleHistoryClick = (session_id) => {
    setSelectedSessionId(session_id); // Set the selected session ID
  };

  // Callback to handle file selection from LeftSidebar
  const handleFileSelection = (files) => {
    setSelectedFiles(files); // Update selected files in state
  };

  return (
    <ThemeProvider>
      <div className="App">

        <div className="container">

          <LeftSidebar history={history} onLogout={onLogout}  setSelectedFolderPath={setSelectedFolderPath}
           onHistoryClick={handleHistoryClick} onFileSelect={handleFileSelection} />
          <MainContent setHistory={setHistory} selectedSessionId={selectedSessionId} selectedFolderPath={selectedFolderPath}
          resetSelectedSessionId={() => setSelectedSessionId(null)}  selectedFiles={selectedFiles} />
          {/* <RightSidebar /> */}
        </div>
      </div>

    </ThemeProvider>
  );
}

export default Dashboard;