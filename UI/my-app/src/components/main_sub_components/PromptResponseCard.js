
import React, { useState } from 'react';
import './PromptResponseCard.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faThumbsUp, faThumbsDown, faCopy, faEdit, faArrowDown } from '@fortawesome/free-solid-svg-icons';

function PromptResponseCard({ item, index, editingIndex, setEditingIndex, handleSubmitEditedPrompt, onSendPrompt }) {
  const [editedPrompt, setEditedPrompt] = useState(item.prompt);
  const [showCopyIcon, setShowCopyIcon] = useState(true);
  const [isThumbsUpActive, setIsThumbsUpActive] = useState(false);
  const [isThumbsDownActive, setIsThumbsDownActive] = useState(false);
  const [comment, setComment] = useState('');
  const [isCommentSubmitted, setIsCommentSubmitted] = useState(false);
  const apiUrl = process.env.REACT_APP_API_URL;

  const handleEditClick = () => {
    setEditingIndex(index);
    setEditedPrompt(item.prompt);
  };

  const handleCopyToClipboard = () => {
    if (item.response) {
      navigator.clipboard.writeText(item.response)
        .then(() => {
          setShowCopyIcon(false);
          setTimeout(() => setShowCopyIcon(true), 2000);
        })
        .catch((err) => console.error("Failed to copy text: ", err));
    }
  };

  // const handleThumbsUpClick = () => {
  //   setIsThumbsUpActive(!isThumbsUpActive);
  //   if (isThumbsDownActive) {
  //     setIsThumbsDownActive(false);
  //     setIsCommentSubmitted(false);
  //   }
  // };

  const handleThumbsUpClick = async () => {
    setIsThumbsUpActive(true);
    if (isThumbsDownActive) {
      setIsThumbsDownActive(false);
      setIsCommentSubmitted(false);
    }
    const token = sessionStorage.getItem('authToken');
  
    try {
      const response = await fetch(`${apiUrl}api/mark_satisfied/${item.id}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        }
      });
  
      if (response.ok) {
        const data = await response.json();
      } else {
        console.error('Failed to mark as satisfied:', response.statusText);
      }
    } catch (error) {
      console.error('Error marking as satisfied:', error);
    }
  };

  // const handleThumbsDownClick = () => {
  //   if (isThumbsDownActive) {
  //     // If thumbs down is already active, deactivate it
  //     setIsThumbsDownActive(false);
  //   } else {
  //     // Set thumbs down active and reset the thumbs up state
  //     setIsThumbsDownActive(true);
  //     setIsThumbsUpActive(false); // Reset thumbs up if thumbs down is clicked
  //   }

  //   setIsCommentSubmitted(false); // Reset comment state whenever thumbs down is clicked
  // };

const handleThumbsDownClick = async () => {
  setIsThumbsDownActive(true);
  setIsThumbsUpActive(false);
  setIsCommentSubmitted(false); 
  const token = sessionStorage.getItem('authToken');

  try {
    const response = await fetch(`${apiUrl}/api/mark_unsatisfied/${item.id}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      console.log(data.message); 
    } else {
      console.error('Failed to mark as unsatisfied:', response.statusText);
    }
  } catch (error) {
    console.error('Error marking as unsatisfied:', error);
  }
};


  const handleCommentSubmit = async () => {
    const token = sessionStorage.getItem('authToken');

    try {
      const response = await fetch(`${apiUrl}/api/save-comment/${item.id}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ comments: comment })
      });

      if (response.ok) {
        const data = await response.json();
        setIsCommentSubmitted(true); // Mark comment as submitted
        setComment(''); // Clear the input
      } else {
        console.error('Failed to submit comment:', response.statusText);
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
    }
  };

  // const handlePdfClick = async () => {
  //   const fileName = "C273.pdf";
  //   const pageNumber = 7;
  //   try {
  //     const response = await fetch(`https://dq2jqf0v-8000.inc1.devtunnels.ms/api/serve-pdf/${fileName}/${pageNumber}/`, {
  //       method: 'GET',
  //       headers: {
  //         'Content-Type': 'application/json',
  //       },
  //     });

  //     console.log('Response Status:', response.status);
  //     console.log('Response:', await response.text()); // Log response text for debugging

  //     if (response.ok) {
  //       // Assuming the backend will return the PDF file as a response
  //       const blob = await response.blob();
  //       const url = URL.createObjectURL(blob);
  //       console.log('PDF URL:', url);

  //       // Open the PDF in a new tab
  //       window.open(url, '_blank');
  //     } else {
  //       console.error("Error fetching PDF:", response.statusText);
  //     }
  //   } catch (error) {
  //     console.error("Error fetching PDF:", error);
  //   }
  // };

  const handlePdfClick = async (fileName, pageNumber) => {
    // const fileName = "ASME SEC V A-7 MPE.pdf";  
    // const pageNumber = 7;        

    // Encode fileName to handle special characters (spaces, etc.)
    const encodedFileName = encodeURIComponent(fileName);

    try {
      // API call to get the PDF from the backend
      const response = await fetch(`${apiUrl}/api/serve-pdf/${encodedFileName}/${pageNumber}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });


      // Check if the response is OK
      if (response.ok) {
        // Convert the response body to a Blob (PDF content)
        const blob = await response.blob();

        // Create a URL for the Blob object
        const pdfUrl = URL.createObjectURL(blob);

        // Open the PDF in a new tab
        window.open(pdfUrl, '_blank');
      } else {
        // Handle the error if the response is not OK
        console.error("Error fetching PDF:", response.statusText);
      }
    } catch (error) {
      // Catch any errors during the fetch operation
      console.error("Error fetching PDF:", error);
    }
  };


  const processResponseLinks = (responseText) => {
    return responseText.split('\n\n').map((part, index) => {
      // Replace the entire source path with a clickable link
      const updatedPart = part.split(/(Source: .*?[\w\s\-_]+\.pdf \| Page: \d+)/g).map((chunk, idx) => {
        if (chunk.match(/Source: .*?([\w\s\-_]+\.pdf) \| Page: (\d+)/)) {
          const [_, fileName, pageNumber] = chunk.match(/Source: .*?([\w\s\-_]+\.pdf) \| Page: (\d+)/);
          return (
            <a key={fileName + pageNumber} href="#" onClick={() => handlePdfClick(fileName, pageNumber)}>
              {chunk}
            </a>
          );
        }
        return chunk; // Return other parts as is
      });
  
      // Return the updated part wrapped in a span, joining array elements back to a string
      return (
        <span key={index}>
          {updatedPart}
          {index !== responseText.split('\n\n').length - 1 && <br />}
        </span>
      );
    });
  };
  

    // const processResponseLinks = (responseText) => {
    //   return responseText.split('\n\n').map((part, index) => {
    //     // Replace the 'Source: ... | Page: ...' pattern with a clickable link
    //     const updatedPart = part.split(/(Source: [\w-]+\.pdf \| Page: \d+)/g).map((chunk, idx) => {
    //       if (chunk.match(/Source: ([\w-]+\.pdf) \| Page: (\d+)/)) {
    //         const [_, fileName, pageNumber] = chunk.match(/Source: ([\w-]+\.pdf) \| Page: (\d+)/);
    //         return (
    //           <a key={fileName + pageNumber} href="#" onClick={() => handlePdfClick(fileName, pageNumber)}>
    //             {chunk}
    //           </a>
    //         );
    //       }
    //       return chunk; // Return other parts as is
    //     });
    
    //     // Return the updated part wrapped in a span, joining array elements back to a string
    //     return (
    //       <span key={index}>
    //         {updatedPart}
    //         {index !== responseText.split('\n\n').length - 1 && <br />}
    //       </span>
    //     );
    //   });
    // };

 
  return (
    <div className="card-container">
      {/* <div className=''>
        <img
          src="/images/profile.png"
          alt="Prompt Avatar"
          className="avatar1"
        />
      </div> */}
      <div className="prompt-card">
        {editingIndex === index ? (
          <div className="edit-prompt-card">
            <input
              type="text"
              className="edit-prompt-input"
              value={editedPrompt}
              onChange={(e) => setEditedPrompt(e.target.value)}
            />
            <button className="save-edit-button" onClick={() => handleSubmitEditedPrompt(editedPrompt, index)}>Send</button>
            <button className="cancel-edit-button" onClick={() => setEditingIndex(null)}>Cancel</button>
          </div>
        ) : (
          <div className="prompt-section">
            <p>{item.prompt}</p>
            <span className="edit-icon" onClick={handleEditClick}>
              <FontAwesomeIcon icon={faEdit} />
            </span>
          </div>
        )}
      </div>
      <img
        src="/images/hacker.png"
        alt="Response Avatar"
        className="avatar2"
      />

      <div className="response-card">
        {/* <p>{item.response || 'Loading...'}</p> */}
        {/* <p>
          {item.response ? (
            item.response.split('\n\n').map((part, index) => (
              <span key={index}>
                {part}
                {index !== item.response.split('\n\n').length - 1 && <br />}
              </span>
            ))
          ) : (
            'Loading...'
          )}
        </p> */}


<p>
      {item.response ? (
        processResponseLinks(item.response)
      ) : (
        'Loading...'
      )}
    </p>

        {/* <button onClick={() => onSendPrompt("Continue")} >Continue</button>

        <button className='pdf-button' onClick={handlePdfClick}>
          Click to open PDF
        </button> */}
        <div className="pdf-button-container">
        
          <div className="continue-container">
            <FontAwesomeIcon icon={faArrowDown} className="arrow-icon" /> {/* Use the imported icon as a component */}
            <a
              href="#"
              className="continue-link"
              onClick={(e) => {
                e.preventDefault(); // Prevent default anchor behavior (page reload)
                onSendPrompt("Continue"); // Trigger your onSendPrompt function
              }}
            >
              Continue
            </a>
          </div>
        </div>


        <div className='thumps'>
          <div className='copy-icon' onClick={handleCopyToClipboard}>
            {showCopyIcon ? (
              <div className="tooltip">
                <FontAwesomeIcon icon={faCopy} />
                {/* <span className="tooltiptext">Copy</span> */}
              </div>
            ) : (
              <span className="copied-message">Copied!</span>
            )}
          </div>
          <div className='thumpsup' onClick={handleThumbsUpClick}>
            <FontAwesomeIcon icon={faThumbsUp} className={isThumbsUpActive ? 'active' : ''} />
          </div>
          <div className='thumpsdown' onClick={handleThumbsDownClick}>
            <FontAwesomeIcon icon={faThumbsDown} className={isThumbsDownActive ? 'active' : ''} />
          </div>
        </div>

        {isThumbsDownActive && !isCommentSubmitted && (
          <div className="comment-box">
            <textarea
              placeholder="Type your comment here..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="comment-input"
            />
            <button onClick={handleCommentSubmit} className="comment-submit-button">Submit</button>
          </div>
        )}
      </div>

      {/* {item.response && item.response !== 'Loading...' && (
        <div>
          <button onClick={() => onSendPrompt("Continue")}>Continue</button>
        </div>
      )} */}
    </div>
  );
}

export default PromptResponseCard;