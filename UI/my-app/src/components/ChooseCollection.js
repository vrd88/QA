import React, { useState, useEffect } from "react";
import "./ChooseCollection.css";


const ChooseCollection = () => {
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState("");
  const [currentCollection, setCurrentCollection] = useState(""); // State to store the current collection
  const [loading, setLoading] = useState(false);

  // Retrieve the token from sessionStorage
  const token = sessionStorage.getItem("authToken");

  // Fetch collections from your Milvus API
  useEffect(() => {
    const fetchCollections = async () => {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/collections/`, {
        headers: {
          "Authorization": `Bearer ${token}`, // Add token in the header
        },
      });
      const data = await response.json();
      setCollections(data.collections); // Assuming response has a `collections` array
    };

    const fetchCurrentCollection = async () => {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/current-using-collection/`, {
        headers: {
          "Authorization": `Bearer ${token}`, // Add token in the header
        },
      });
      const data = await response.json();
      setCurrentCollection(data.current_using_collection || "No collection selected");
    };

    fetchCollections();
    fetchCurrentCollection();
  }, [token]); // Re-run the effect if token changes

  // Handle dropdown change
  const handleCollectionChange = (e) => {
    setSelectedCollection(e.target.value);
  };

  // Handle "Next" button click
  const handleChangeClick = async () => {
    if (selectedCollection === "") {
      alert("Please select a collection first!");
      return;
    }

    const userConfirmed = window.confirm(
      `Are you sure you want to change the current collection to "${selectedCollection}"?`
    );

    if (userConfirmed) {
      try {
        // Send the selected collection to the backend to update the current collection
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/update-current-collection/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`, // Add token in the header
          },
          body: JSON.stringify({ current_using_collection: selectedCollection }),
        });

        if (response.ok) {
          setCurrentCollection(selectedCollection); // Update current collection state
          alert("Successfully changed collection!");
        } else {
          alert("Failed to change collection. Please try again.");
        }
      } catch (error) {
        alert("An error occurred while updating the collection.");
      }
    }
  };
  const restartServer = async () => {
    try {
      // Ask for confirmation before proceeding
      const userConfirmed = window.confirm("Are you sure you want to restart the server?");
  
      if (!userConfirmed) {
        alert("Server restart canceled.");
        return; // Stop the function if the user cancels
      }
  
      // Retrieve the token from sessionStorage
      const token = sessionStorage.getItem('authToken');
    
      if (!token) {
        alert("No authentication token found. Please log in again.");
        return;
      }
      setLoading(true);
      // Make the API call to restart the server
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/restart-server/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`, // Add token in the header
        },
      });
    
      const data = await response.json();
    
      if (response.ok) {
        setLoading(false);
        alert("Successfully restarted."); 
      } else {
        alert(`Failed to restart server: ${data.message}`);
      }
    } catch (error) {
      console.error('Error restarting the server:', error);
      setLoading(false);
      alert("Successfully restarted..");
    } 
  };
  
  
  return (
    <div>
     {loading && (
        <div className="loading-gif" >
          <img className="load-img" src="/images/loading_gif.gif" alt="Loading..." />
        </div>
      )}
<div className="collection-container">
  <div className="current-collection">
    <span>Current Selected Collection: </span>
    <span className="sp">{currentCollection}</span> {/* Display current collection */}
  </div>

  <div className="collection-selection">
    <label className="collection-label">Change Collection</label>
    <select 
      className="collection-dropdown" 
      value={selectedCollection} 
      onChange={handleCollectionChange}
    >
      <option value="">--Select a Collection--</option>
      {collections.map((collection, index) => (
        <option key={index} value={collection}>
          {collection}
        </option>
      ))}
    </select>
  </div>

  <div className="button-group">
    <button 
      className={`button ${!selectedCollection ? "button-disabled" : ""}`} 
      onClick={handleChangeClick} 
      disabled={!selectedCollection}
    >
      Change
    </button>
    <button className="button restart-button" onClick={restartServer}>
      Restart Server
    </button>
  </div>
</div>


    </div>
  );
};

export default ChooseCollection;
