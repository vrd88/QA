
import React, { useState, useEffect, useRef, useCallback} from 'react';
import './MainContent.css';
import PromptResponseCard from './main_sub_components/PromptResponseCard';
import ChatControls from './main_sub_components/ChatControls';
import NavBar from './NavBar';

function MainContent({ setHistory, selectedSessionId, resetSelectedSessionId, selectedFiles, selectedFolderPath }) {
  const [prompt, setPrompt] = useState('');
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);
  // const responseEndRef = useRef(null);
  const [sessionId, setSessionId] = useState(null);
  const apiUrl = process.env.REACT_APP_API_URL;

  console.log(selectedFolderPath);
  const token = sessionStorage.getItem('authToken');
  // Function to handle input change
  const handleInputChange = (e) => {
    setPrompt(e.target.value);
  };

  // Function to handle new chat
  const handleNewChat = () => {
    setResponses([]);
    setPrompt('');
    setEditingIndex(null);
    setSessionId(null);
    resetSelectedSessionId();

    // Fetch history API when new chat is started
    // fetch(`${apiUrl}/api/history/`, {
    //   headers: { Authorization: `Bearer ${token}` }
    // })
    //   .then((res) => res.json())
    //   .then((data) => setHistory(data || []))
    //   .catch((error) => console.error('Error fetching history:', error));
  };

  // const simulateTypingEffect = (fullResponse, index) => {
  //   let currentResponse = '';
  //   let charIndex = 0;

  //   const typingInterval = setInterval(() => {
  //     if (charIndex < fullResponse.length) {
  //       currentResponse += fullResponse[charIndex];
  //       setResponses((prevResponses) => {
  //         const updatedResponses = [...prevResponses];
  //         updatedResponses[index].response = currentResponse;
  //         return updatedResponses;
  //       });
  //       charIndex++;
  //     } else {
  //       clearInterval(typingInterval);
  //     }
  //   }, 10);
  // };

  const handleSendPrompt = async (promptToSend) => {
    if (!promptToSend) return;
  
    setLoading(true); // Set loading to true to indicate waiting
  
    const newResponseEntry = {
      prompt: promptToSend,
      response: '',
      loading: true,
    };
    
    // Add a new response entry with loading state to the responses array
    setResponses((prevResponses) => [...prevResponses, newResponseEntry]);
    setPrompt('');
    try {
      const fileNames = selectedFiles.map((file) => file);
      const requestData = {
        prompt: promptToSend,
        session_id: sessionId || selectedSessionId,
        file_names: fileNames,
        jwt_token: token,
        selectedFolderPath: selectedFolderPath,
      };
      
  
      const res = await fetch(`${apiUrl}/api/cohere/generate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });
      
      const historyId = res.headers.get('X-History-ID');
      const sessionIdFromHeader = res.headers.get('X-Session-ID');
    
  
      setSessionId(sessionIdFromHeader || selectedSessionId);
  
      // Handle streaming the partial responses
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let responseChunks = []; 
  
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
  
        if (done) {
          // console.log('All chunks received. Finalizing response...');
        }
  
        // Decode and append the response chunk to the array
        const chunk = decoder.decode(value, { stream: true });
  
        if (chunk.trim()) {
           // Check for the pattern and replace it with a clickable link
        //   const linkPattern = /Source:\s*(\S+_\S+\.pdf)\s*\|\s*Page:\s*(\d+)/g;
        //   const updatedChunk = chunk.replace(linkPattern, (match, fileName, pageNumber) => {
        //   // Create a clickable link
        //   return `<a href="#" onClick="fetchpdf('${fileName}', ${pageNumber})">Source: ${fileName} | Page: ${pageNumber}</a>`;
        // });
          responseChunks = [...responseChunks, chunk]; 
          // console.log('Updated responseChunks array:', responseChunks); 
        }
  
        if (chunk.includes('      '))  {
          // console.log('All chunks received. Finalizing response...');
          done = true; 
          continue;
        }
  
        setResponses((prevResponses) => {
          const updatedResponse = {
            prompt: promptToSend,
            response: responseChunks.join(' '), 
            loading: true, 
            id: historyId || null,
          };
  
          // console.log('Updated responses state with partial response:', updatedResponse);
  
          return [...prevResponses.slice(0, -1), updatedResponse];
        });
      }
      
      
      // console.log('All chunks received. Finalizing response...');
      fetch(`${apiUrl}/api/history/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then((res) => res.json())
        .then((data) => setHistory(data || []))
        .catch((error) => console.error('Error fetching history:', error));
      setLoading(false); 
  
      // Log and update the final response
      setResponses((prevResponses) => {
        const finalResponse = {
          prompt: promptToSend,
          response: responseChunks.join(' '), 
          loading: false, 
          id: historyId || null,
        };
  
        // console.log('Final responses state:', [...prevResponses.slice(0, -1), finalResponse]);
  
        return [...prevResponses.slice(0, -1), finalResponse];
      });
  

      setPrompt('');
  
    } catch (error) {
      console.error('Error:', error);
      setLoading(false);
      setResponses((prevResponses) => {
        const errorResponse = {
          prompt: promptToSend,
          response: 'An error occurred',
          loading: false,
        };
  
        console.log('Error responses state:', [...prevResponses.slice(0, -1), errorResponse]);
        return [...prevResponses.slice(0, -1), errorResponse];
      });
  
      // Clear the input field even if there's an error
      setPrompt('');
    }
  };

  
  // Initial call to fetch history when component loads
  useEffect(() => {
    fetch(`${apiUrl}/api/history/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((res) => res.json())
      .then((data) => setHistory(data || []))
      .catch((error) => console.error('Error fetching history:', error));
  }, [setHistory,apiUrl,token]);

  // const fetchSessionHistory = (session_id) => {
  //   fetch(`${apiUrl}/api/history/${session_id}/`, {
  //     headers: { Authorization: `Bearer ${token}` }
  //   })
  //     .then((res) => res.json())
  //     .then((data) => {
  //       const sessionData = (data || []).map((item) => ({
  //         prompt: item.prompt,
  //         response: item.response,
  //         loading: false,
  //         id: item.id,
  //       }));

  //       setResponses(sessionData);
  //       setSessionId(session_id);
  //     })
  //     .catch((error) => console.error('Error fetching session history:', error));
  // };

  // useEffect(() => {
  //   if (selectedSessionId) {
  //     fetchSessionHistory(selectedSessionId);
  //   }
  // }, [selectedSessionId]);

const fetchSessionHistory = useCallback((session_id) => {
  fetch(`${apiUrl}/api/history/${session_id}/`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((res) => res.json())
    .then((data) => {
      const sessionData = (data || []).map((item) => ({
        prompt: item.prompt,
        response: item.response,
        loading: false,
        id: item.id,
      }));

      setResponses(sessionData);
      setSessionId(session_id);
    })
    .catch((error) =>
      console.error('Error fetching session history:', error)
    );
}, [apiUrl, token, setResponses, setSessionId]);

useEffect(() => {
  if (selectedSessionId) {
    fetchSessionHistory(selectedSessionId);
  }
}, [selectedSessionId, fetchSessionHistory]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendPrompt(prompt);
    }
  };

  // useEffect(() => {
  //   if (responseEndRef.current) {
  //     responseEndRef.current.scrollIntoView({ behavior: 'smooth' });
  //   }
  // }, [responses]);
   // Handle scroll event inside the container

   const responseEndRef = useRef(null);
   const prevResponseCountRef = useRef(0); // Track previous response count
 
   useEffect(() => {
     // Check if a new response has been added
     if (responses.length > prevResponseCountRef.current) {
       // Scroll to the latest prompt and response card
       if (responseEndRef.current) {
         responseEndRef.current.scrollIntoView({ behavior: 'smooth' });
       }
     }
 
     // Update the previous response count to current
     prevResponseCountRef.current = responses.length;
   }, [responses]); 
 
   

  const handleSubmitEditedPrompt = async (newPrompt, index) => {
    let updatedResponses = [...responses];
    updatedResponses[index] = {
      ...updatedResponses[index],
      prompt: newPrompt,
      response: '',
      loading: true,
    };
    setResponses(updatedResponses);
  
    try {
      // Prepare the file names just like in handleSendPrompt
      const fileNames = selectedFiles.map((file) => file);
  
      // Send the updated request with files
      const requestData = {
        prompt: newPrompt,
        session_id: sessionId,
        file_names: fileNames, // Include the files as part of the request
      };
  
      setEditingIndex(null);
      const res = await fetch(`${apiUrl}/api/cohere/generate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });
  
      const historyId = res.headers.get('X-History-ID');
      const sessionIdFromHeader = res.headers.get('X-Session-ID');
     
  
      setSessionId(sessionIdFromHeader || sessionId);
  
      // Handle streaming the partial responses
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let responseChunks = [];
  
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        const chunk = decoder.decode(value, { stream: true });
  
        if (chunk.trim()) {
          responseChunks = [...responseChunks, chunk];
        }
  
        // Stop the loop if the terminating condition is met
        if (chunk.includes('      ') || doneReading) {
          // console.log('All chunks received. Finalizing response...');
          done = true;
          continue;
        }
  
        setResponses((prevResponses) => {
          const updatedResponse = {
            ...prevResponses[index],
            response: responseChunks.join(' '),
            loading: true,
          };
          const newResponses = [...prevResponses];
          newResponses[index] = updatedResponse;
          return newResponses;
        });
      }
  
      // Finalize the response
      setResponses((prevResponses) => {
        const finalResponse = {
          ...prevResponses[index],
          response: responseChunks.join(' '),
          loading: false,
        };
        const newResponses = [...prevResponses];
        newResponses[index] = finalResponse;
        return newResponses;
      });
  
     
    } catch (error) {
      updatedResponses[index].response = 'An error occurred';
      updatedResponses[index].loading = false;
      setResponses(updatedResponses);
    }
  };
  
  

  return (
    <div className="main-container">
      <NavBar />
      {/* <div className="logo-container">
        {responses.length > 0 ? (
          <div className="responses-list">
            {responses.map((item, index) => (
              <PromptResponseCard
                key={item.id}
                item={item}
                index={index}
                editingIndex={editingIndex}
                setEditingIndex={setEditingIndex}
                handleSubmitEditedPrompt={handleSubmitEditedPrompt}
              />
            ))}
            <div ref={responseEndRef} />
          </div>
        ) : (
          <h1 className="saarthi-logo">SAARTHI</h1>
        )}
      </div> */}
      <div className="logo-container">
        {responses.length > 0 ? (
          
          <div className="responses-list"  >
            {responses.map((item, index) => {
              // Log the current item and its index
              // console.log('Item:', item);
              // console.log('Index:', index);
              // console.log('responses:', responses);

              return (
                <PromptResponseCard
                  key={item.id}
                  item={item}
                  index={index}
                  editingIndex={editingIndex}
                  setEditingIndex={setEditingIndex}
                  handleSubmitEditedPrompt={handleSubmitEditedPrompt}
                  onSendPrompt={handleSendPrompt} 
                />
              ); 
            })}
            <div ref={responseEndRef} />
          </div>
        ) : (
          <h1 className="saarthi-logo"> </h1>
        )}
      </div>


      <ChatControls
        prompt={prompt}
        handleInputChange={handleInputChange}
        handleKeyPress={handleKeyPress}
        handleSendPrompt={handleSendPrompt}
        handleNewChat={handleNewChat}
      />

      <p className="disclaimer">
        Correctness of response depends on the probabilistic nature of the model. For more precise and accurate information, please refer to the actual document!
      </p>
    </div>
  );
}

export default MainContent;