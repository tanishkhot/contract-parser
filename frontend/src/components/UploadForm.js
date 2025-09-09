import React, { useState } from 'react';

function UploadForm({ onUploadSuccess }) { // Receive onUploadSuccess prop
  const [highlight, setHighlight] = useState(false);
  const [message, setMessage] = useState('');

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setHighlight(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setHighlight(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const uploadFile = async (file) => {
    setMessage(`Uploading ${file.name}...`);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/contracts/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setMessage(`File ${file.name} uploaded successfully! Contract ID: ${data.contract_id}`);
        if (onUploadSuccess) {
          onUploadSuccess(); // Call the refresh function
        }
      } else {
        const errorData = await response.json();
        setMessage(`Failed to upload ${file.name}: ${errorData.detail || response.statusText}`);
      }
    } catch (error) {
      setMessage(`Error uploading ${file.name}: ${error.message}`);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setHighlight(false);

    const files = [...e.dataTransfer.files];
    if (files.length > 0) {
      uploadFile(files[0]); // Assuming only one file for now
    }
  };

  const handleFileSelect = (e) => {
    const files = [...e.target.files];
    if (files.length > 0) {
      uploadFile(files[0]); // Assuming only one file for now
    }
  };

  return (
    <div
      className={`upload-area ${highlight ? 'highlight' : ''}`}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${highlight ? '#007bff' : '#ccc'}`,
        borderRadius: '5px',
        padding: '20px',
        textAlign: 'center',
        cursor: 'pointer',
        margin: '20px auto',
      }}
    >
      <p>Drag 'n' drop some PDF files here, or click to select files</p>
      <input
        type="file"
        accept=".pdf"
        style={{ display: 'none' }}
        id="fileInput"
        onChange={handleFileSelect}
      />
      <label htmlFor="fileInput" style={{
        backgroundColor: '#007bff',
        color: 'white',
        padding: '10px 15px',
        borderRadius: '5px',
        cursor: 'pointer',
        marginTop: '10px',
        display: 'inline-block',
      }}>
        Select File
      </label>
      {message && <p style={{ marginTop: '15px', color: message.includes('Error') || message.includes('Failed') ? 'red' : 'green' }}>{message}</p>}
    </div>
  );
}

export default UploadForm;
