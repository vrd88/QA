import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './LeftSidebar.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHistory, faCloudArrowUp, faSignOutAlt } from '@fortawesome/free-solid-svg-icons';
import Select from 'react-select';
import { useContext } from 'react';
import { ThemeContext } from './main_sub_components/ThemeProvider';
import { faMoon, faSun } from '@fortawesome/free-solid-svg-icons';

function LeftSidebar({ history, onHistoryClick, onFileSelect, onLogout, setSelectedFolderPath}) {
  const navigate = useNavigate();
  const [selectedOptions, setSelectedOptions] = useState([]);
  const [userName, setUserName] = useState('');
  const [options, setOptions] = useState([]);
  const { isDarkMode, toggleDarkMode } = useContext(ThemeContext);
  const apiUrl = process.env.REACT_APP_API_URL;


  // Fetch the username from localStorage when the component mounts
  useEffect(() => {
    const storedUserName = sessionStorage.getItem('userName');
    if (storedUserName) {
      const formattedUserName = storedUserName.charAt(0).toUpperCase() + storedUserName.slice(1).toLowerCase();
      setUserName(formattedUserName);
    }
  }, []);

  // Fetch options from the backend API
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/documents/`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${sessionStorage.getItem('authToken')}`, // Include the auth token here
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          const formattedOptions = data['files'].map(doc => ({
            value: doc,
            label: doc.substring(doc.lastIndexOf('/') + 1),
          }));
          setOptions(formattedOptions);
        } else {
          console.error('Failed to fetch options');
        }
      } catch (error) {
        console.error('Error fetching options:', error);
      }
    };

    fetchOptions();
  }, [apiUrl]);


  const handleChange = (selected) => {
    setSelectedOptions(selected);

    // Send the selected files to the parent (Dashboard) component
    const selectedFiles = selected ? selected.map(option => option.value) : [];
    onFileSelect(selectedFiles);
  };

  // const handleLogout = async () => {
  //   try {
  //     const response = await fetch(`${apiUrl}api/logout/`, {
  //       method: 'POST',
  //       headers: {
  //         'Content-Type': 'application/json',
  //         'Authorization': `Bearer ${sessionStorage.getItem('authToken')}`,
  //       },
  //       body: JSON.stringify({
  //         refresh: sessionStorage.getItem('refreshToken'),
  //       }),
  //     });

  //     if (response.ok) {
  //       sessionStorage.removeItem('authToken');
  //       sessionStorage.removeItem('refreshToken');
  //       navigate('/login');
  //     } else {
  //       console.error('Logout failed');
  //     }
  //   } catch (error) {
  //     console.error('Error during logout:', error);
  //   }
  // };

  const handleLogout = async () => {
    try {
      const response = await fetch(`${apiUrl}api/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({
          refresh: sessionStorage.getItem('refreshToken'),
        }),
      });

      if (response.ok) {

      } else {

      }
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      // Clear session storage
      sessionStorage.removeItem('authToken');
      sessionStorage.removeItem('refreshToken');
      sessionStorage.clear();

      // Update parent state via onLogout and navigate to login
      onLogout();
      navigate('/login'); // Ensures user is redirected to login page
    }
  };

  const [folderTree, setFolderTree] = useState({});
  const [currentPath, setCurrentPath] = useState([]); // Tracks the current folder path
  const [subfolders, setSubfolders] = useState([]); // Subfolders for the current path
  const [filteredSubfolders, setFilteredSubfolders] = useState([]); // Filtered folders for search
  const [inputValue, setInputValue] = useState(""); // The input field showing the full path
  const [error, setError] = useState(null); // For any errors
  const [isDropdownOpen, setIsDropdownOpen] = useState(false); // Tracks dropdown visibility

  // Build folder tree utility
  const buildFolderTree = (folderArray) => {
    const tree = {};

    folderArray.forEach((path) => {
      const parts = path.split("/").filter((part) => part !== "");
      let currentLevel = tree;

      parts.forEach((part) => {
        if (!currentLevel[part]) {
          currentLevel[part] = {};
        }
        currentLevel = currentLevel[part];
      });
    });

    return tree;
  };

  // Get subfolders utility
  const getSubfolders = (tree, pathArray) => {
    let currentLevel = tree;
    for (const part of pathArray) {
      currentLevel = currentLevel[part] || {};
    }
    return Object.keys(currentLevel);
  };

  // Fetch folder structure from the backend with token
  useEffect(() => {
    const fetchFolders = async () => {
      try {
        const token = sessionStorage.getItem("authToken");
        if (!token) {
          throw new Error("No authentication token found");
        }

        const response = await fetch(`${apiUrl}/api/folder_name/`, {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`, // Pass the token in the header
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (!data.folder || !Array.isArray(data.folder)) {
          throw new Error("Invalid folder data format");
        }

        const tree = buildFolderTree(data.folder);
        setFolderTree(tree);
        setSubfolders(Object.keys(tree)); // Initially show the top-level folders
        setFilteredSubfolders(Object.keys(tree)); // Initialize filtered subfolders
      } catch (err) {
        setError(err.message);
      }
    };

    fetchFolders();
  }, [apiUrl]);

  const handleSelectFolder = (folder) => {
    const newPath = [...currentPath, folder];
    const updatedPath = newPath.join("/") + "/"; // Append '/' to the end
    setCurrentPath(newPath);
    setInputValue(updatedPath); // Update the input field with the selected path
    const updatedSubfolders = getSubfolders(folderTree, newPath); // Update the subfolder list
    setSubfolders(updatedSubfolders);
    setFilteredSubfolders(updatedSubfolders);
    setIsDropdownOpen(true); // Ensure dropdown remains open after selection
    setSelectedFolderPath(updatedPath);
  };

  // Handle resetting the path
  const handleReset = () => {
    setCurrentPath([]);
    setInputValue("");
    setSubfolders(Object.keys(folderTree)); // Reset to the top-level folders
    setFilteredSubfolders(Object.keys(folderTree)); // Reset filtered subfolders
    setIsDropdownOpen(false); // Close the dropdown
  };

  // Handle input click to toggle the dropdown
  const handleInputClick = () => {
    setFilteredSubfolders(getSubfolders(folderTree, currentPath)); // Update subfolders
    setIsDropdownOpen((prev) => !prev); // Toggle dropdown visibility
  };

  // Handle input typing to filter subfolders
  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);
    // setSelectedFolderPath(value);

    const filtered = subfolders.filter((folder) =>
      folder.toLowerCase().includes(value.toLowerCase())
    );
    setFilteredSubfolders(filtered);
    setIsDropdownOpen(true); // Show dropdown when typing
  };

  

  return (
    <div className="left-sidebar">
      <div className="new">
        <img src="/images/L&T PES - Linear Logo - Black.jpg" alt="A descriptive alt text" className='lnt-logo' />
      </div>
      
{/* 
      <div className="folder-selector-container">
      <h3 className="folder-selector-heading">Choose Folder</h3>

      {error && <div className="error-message">Error: {error}</div>}

      <div className="input-container">
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange} // Handle typing and search
          placeholder="Select a folder"
          onClick={handleInputClick} // Toggle dropdown on click
          className="folder-input"
        />

        {inputValue && (
          <span onClick={handleReset} className="reset-icon">
            &times;
          </span>
        )}
      </div>

      {isDropdownOpen && filteredSubfolders.length > 0 && (
        <div className="dropdown-container">
          {filteredSubfolders.map((folder) => (
            <div
              key={folder}
              className="folder-item"
              onClick={() => handleSelectFolder(folder)} // Select the folder
            >
              {folder}
            </div>
          ))}
        </div>
      )}
    </div> */}






      <div className="multi-select">
        <Select
          isMulti
          name="options"
          options={options}
          value={selectedOptions}
          onChange={handleChange}
          className="multi-select"
        />
      </div>

      {/* <label className="custom-file-input">
        <FontAwesomeIcon icon={faCloudArrowUp} className="upload" />
        Upload document
        <input type="file" />
      </label> */}

      <div className="history-section">
        <h4>Today</h4>
        <ul>
          {history.today.map((item) => (
            <li key={item.id} onClick={() => onHistoryClick(item.session_id)}>
              <FontAwesomeIcon icon={faHistory} className="history-icon" />
              {item.prompt}
            </li>
          ))}
        </ul>

        <h4>Yesterday</h4>
        <ul>
          {history.yesterday.map((item) => (
            <li key={item.id} onClick={() => onHistoryClick(item.session_id)}>
              <FontAwesomeIcon icon={faHistory} className="history-icon" />
              {item.prompt}
            </li>
          ))}
        </ul>

        <h4>Last Week</h4>
        <ul>
          {history.last_week.map((item) => (
            <li key={item.id} onClick={() => onHistoryClick(item.session_id)}>
              <FontAwesomeIcon icon={faHistory} className="history-icon" />
              {item.prompt}
            </li>
          ))}
        </ul>

        <h4>Last Month</h4>
        <ul>
          {history.last_month.map((item) => (
            <li key={item.id} onClick={() => onHistoryClick(item.session_id)}>
              <FontAwesomeIcon icon={faHistory} className="history-icon" />
              {item.prompt}
            </li>
          ))}
        </ul>
      </div>

      <div className="progress-bar"></div>

      <div className="user-card-container">
        <div className="user-details">
          <img
            src="/images/ai-technology.png"
            alt="User Avatar"
            className="user_avatar"
          />
          <span className="user-name">{userName || 'Guest'}</span>
          <div className="user-actions">
            
              {/* Dark Mode Toggle with Tooltip */}
              <div className="icon-with-tooltip">
                <FontAwesomeIcon
                  icon={isDarkMode ? faSun : faMoon}
                  className="user-icon"
                  onClick={toggleDarkMode}
                />
                <span className="tooltip-text">{isDarkMode ? "Light Mode" : "Dark Mode"}</span>
              </div>

              {/* Logout Icon with Tooltip */}
              <div className="icon-with-tooltip">
                <FontAwesomeIcon
                  icon={faSignOutAlt}
                  className="user-icon"
                  onClick={handleLogout}
                />
                <span className="tooltip-text">Logout</span>
              </div>
           

          </div>
        </div>

      </div>
    </div>
  );
}

export default LeftSidebar;