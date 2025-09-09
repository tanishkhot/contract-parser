import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import { Route, Routes, useNavigate } from 'react-router-dom'; // Remove BrowserRouter as Router
import UploadForm from './components/UploadForm';
import ContractList from './components/ContractList';
import ContractDetail from './components/ContractDetail';

function App() {
  const [contracts, setContracts] = useState([]);
  const [searchId, setSearchId] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [searchError, setSearchError] = useState('');
  const navigate = useNavigate(); // Initialize useNavigate

  const fetchContracts = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/contracts');
      if (response.ok) {
        const data = await response.json();
        // Map the data to include contract_id from _id
        const formattedContracts = data.map(contract => ({
          ...contract,
          contract_id: contract._id // Use _id as contract_id
        }));
        setContracts(formattedContracts);
      } else {
        console.error('Failed to fetch contracts:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching contracts:', error);
    }
  }, []);

  useEffect(() => {
    fetchContracts();
    const interval = setInterval(fetchContracts, 5000);
    return () => clearInterval(interval);
  }, [fetchContracts]);

  const handleSearch = async () => {
    setSearchResult(null);
    setSearchError('');
    if (!searchId) {
      setSearchError('Please enter a Contract ID.');
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/contracts/${searchId}/status`);
      if (response.ok) {
        const data = await response.json();
        setSearchResult({ id: searchId, status: data.status });
      } else {
        const errorData = await response.json();
        setSearchError(errorData.detail || 'Contract not found or error fetching status.');
      }
    } catch (error) {
      setSearchError(`Error searching: ${error.message}`);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Contract Intelligence Parser</h1>
      </header>
      <main>
        <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #eee', borderRadius: '8px', backgroundColor: '#f9f9f9' }}>
          <h3>Search Contract by ID</h3>
          <input
            type="text"
            placeholder="Enter Contract ID"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            style={{ padding: '8px', marginRight: '10px', borderRadius: '4px', border: '1px solid #ddd', width: '300px' }}
          />
          <button onClick={handleSearch} style={{ padding: '8px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Search</button>
          {searchError && <p style={{ color: 'red', marginTop: '10px' }}>{searchError}</p>}
          {searchResult && (
            <div style={{ marginTop: '10px' }}>
              <p><strong>Contract ID:</strong> {searchResult.id}</p>
              <p><strong>Status:</strong> {searchResult.status}</p>
              <button onClick={() => navigate(`/contracts/${searchResult.id}`)} style={{ padding: '8px 15px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', marginTop: '10px' }}>View Details</button>
            </div>
          )}
        </div>

        <Routes>
          <Route path="/" element={
            <>
              <UploadForm onUploadSuccess={fetchContracts} />
              <ContractList contracts={contracts} />
            </>
          } />
          <Route path="/contracts/:contractId" element={<ContractDetail />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
