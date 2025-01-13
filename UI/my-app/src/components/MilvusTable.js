
// import React, { useState, useEffect } from "react";
// import './MilvusTable.css'; // Import the CSS

// const MilvusTable = ({ collectionName, onClose }) => {
//   const [data, setData] = useState([]);
//   const [filteredData, setFilteredData] = useState([]); // To store the filtered data based on search
//   const [searchQuery, setSearchQuery] = useState(""); // Search query state
//   const [page, setPage] = useState(1);
//   const [loading, setLoading] = useState(false);
//   const [isVisible, setIsVisible] = useState(true); // State to manage visibility of the table
//   const apiUrl = process.env.REACT_APP_API_URL;

//   const fetchData = async (collectionName) => {
//     setLoading(true);
//     const token = sessionStorage.getItem("authToken");
//     if (!token) {
//       alert("No authentication token found");
//       return;
//     }

//     try {
//       const response = await fetch(
//         `${apiUrl}/api/milvus-data/${collectionName}/`,
//         {
//           method: "GET",
//           headers: {
//             Authorization: `Bearer ${token}`,
//           },
//         }
//       );
//       const result = await response.json();
//       setData(result.data);
//       setFilteredData(result.data); // Set the filtered data initially to all data
//       setPage(result.page);
//     } catch (error) {
//       console.error("Error fetching data:", error);
//       alert("Failed to fetch data.");
//     }
//     setLoading(false);
//   };

//   useEffect(() => {
//     if (collectionName) {
//       fetchData(collectionName);
//     }
//   }, [collectionName, page]);

//   // Handle search query change
//   const handleSearch = (e) => {
//     const query = e.target.value.toLowerCase();
//     setSearchQuery(query);

//     // Filter data based on the source field
//     const filtered = data.filter((row) =>
//       row.source.toLowerCase().includes(query)
//     );
//     setFilteredData(filtered); // Set the filtered data
//   };

//   const handleNextPage = () => {
//     setPage((prevPage) => prevPage + 1);
//   };

//   const handlePreviousPage = () => {
//     if (page > 1) setPage((prevPage) => prevPage - 1);
//   };

//   return (
//     <div className="milvus-table">
//       <div className="milvus-table-header">
//         <button className="close-button1" onClick={onClose}>
//           ✖
//         </button>
//       </div>
//       <input
//         type="text"
//         placeholder="Search by source..."
//         value={searchQuery}
//         onChange={handleSearch}
//         className="search-bar"
//       />
//       {loading ? (
//         <p className="loading">Loading...</p>
//       ) : (
//         <div className="scrollable-table">
//           <table className="milvus-table-table">
//             <thead>
//               <tr>
//                 <th>Serial No</th>
//                 <th>Source</th>
//                 <th>Page</th>
//                 <th>Text</th>
//               </tr>
//             </thead>
//             <tbody>
//               {filteredData.map((row, index) => (
//                 <tr key={index}>
//                   <td>{index + 1}</td>
//                   <td>{row.source}</td>
//                   <td>{row.page}</td>
//                   <td>{row.text}</td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>
//       )}
//       <div className="pagination-container">
//         <button
//           onClick={handlePreviousPage}
//           disabled={page === 1}
//           className="pagination-button"
//         >
//           Previous
//         </button>
//         <span className="page-number">Page: {page}</span>
//         <button
//           onClick={handleNextPage}
//           className="pagination-button"
//         >
//           Next
//         </button>
//       </div>
//     </div>
//   );
// };




import React, { useState, useEffect } from "react";
import './MilvusTable.css'; // Import the CSS

const MilvusTable = ({ collectionName, onClose }) => {
  const [data, setData] = useState([]); // All fetched data
  const [filteredData, setFilteredData] = useState([]); // Data to be shown (filtered or all)
  const [searchQuery, setSearchQuery] = useState(""); // Search query state
  const [page, setPage] = useState(1); // Tracks the current page
  const [loading, setLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const apiUrl = process.env.REACT_APP_API_URL;

  const fetchData = async (collectionName, page) => {
    setLoading(true);
    const token = sessionStorage.getItem("authToken");
    if (!token) {
      alert("No authentication token found");
      return;
    }

    try {
      const response = await fetch(
        `${apiUrl}/api/milvus-data/${collectionName}/?page=${page}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const result = await response.json();

      // Append new data to the existing data if the page is greater than 1
      if (page > 1) {
        setData((prevData) => [...prevData, ...result.data]);
        setFilteredData((prevData) => [...prevData, ...result.data]);
      } else {
        // If it's the first page, replace the data
        setData(result.data);
        setFilteredData(result.data);
      }

      setPage(result.page); // Set the current page
    } catch (error) {
      console.error("Error fetching data:", error);
      alert("Failed to fetch data.");
    }
    setLoading(false);
  };

  useEffect(() => {
    if (collectionName) {
      fetchData(collectionName, page);
    }
  }, [collectionName, page]);

  // Handle search query change
  const handleSearch = (e) => {
    const query = e.target.value.toLowerCase();
    setSearchQuery(query);

    // Filter data based on the source field
    const filtered = data.filter((row) =>
      row.source.toLowerCase().includes(query)
    );
    setFilteredData(filtered); // Set the filtered data
  };

  const handleNextPage = () => {
    setPage((prevPage) => prevPage + 1); // Go to next page
  };

  const handlePreviousPage = () => {
    if (page > 1) setPage((prevPage) => prevPage - 1); // Go to previous page
  };

  return (
    <div className="milvus-table">
      <div className="milvus-table-header">
        <button className="close-button1" onClick={onClose}>
          ✖
        </button>
      </div>
      <input
        type="text"
        placeholder="Search by source..."
        value={searchQuery}
        onChange={handleSearch}
        className="search-bar"
      />
      {loading ? (
        <p className="loading">Loading...</p>
      ) : (
        <div className="scrollable-table">
          <table className="milvus-table-table">
            <thead>
              <tr>
                <th>Serial No</th>
                <th>Source</th>
                <th>Page</th>
                <th>Text</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((row, index) => (
                <tr key={index}>
                  <td>{index + 1 + (page - 1) * 150}</td> {/* Add serial number offset */}
                  <td>{row.source}</td>
                  <td>{row.page}</td>
                  <td>{row.text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="pagination-container">
        <button
          onClick={handlePreviousPage}
          disabled={page === 1}
          className="pagination-button"
        >
          Previous
        </button>
        <span className="page-number">Page: {page}</span>
        <button
          onClick={handleNextPage}
          className="pagination-button"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default MilvusTable;
