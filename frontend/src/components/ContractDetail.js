import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

function ContractDetail() {
  const { contractId } = useParams();
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchContractDetail = async () => {
      try {
        const response = await fetch(`http://localhost:8000/contracts/${contractId}`);
        if (response.ok) {
          const data = await response.json();
          setContract(data);
        } else {
          setError(`Failed to fetch contract details: ${response.statusText}`);
        }
      } catch (err) {
        setError(`Error fetching contract details: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchContractDetail();
  }, [contractId]);

  if (loading) {
    return <p>Loading contract details...</p>;
  }

  if (error) {
    return <p style={{ color: 'red' }}>Error: {error}</p>;
  }

  if (!contract) {
    return <p>Contract not found.</p>;
  }

  return (
    <div style={{ textAlign: 'left', margin: '20px auto', maxWidth: '800px', border: '1px solid #eee', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <Link to="/" style={{ display: 'block', marginBottom: '20px', color: '#007bff', textDecoration: 'none' }}>&larr; Back to Contract List</Link>
      <h2>Contract Details: {contract.contract_id}</h2>
      <p><strong>Status:</strong> {contract.status}</p>

      {contract.status === 'completed' && contract.extracted_data ? (
        <div>
          <h3>Extracted Data</h3>
          {Object.entries(contract.extracted_data).map(([category, data]) => (
            <div key={category} style={{ marginBottom: '15px', borderBottom: '1px dashed #eee', paddingBottom: '10px' }}>
              <h4>{category.replace(/_/g, ' ').toUpperCase()}</h4>
              {Object.entries(data).map(([key, value]) => (
                <p key={key} style={{ margin: '5px 0' }}>
                  <strong>{key.replace(/_/g, ' ')}:</strong> {JSON.stringify(value)}
                </p>
              ))}
            </div>
          ))}
          {contract.confidence_score && (
            <p><strong>Confidence Score:</strong> {contract.confidence_score.toFixed(2)}</p>
          )}
          {contract.gap_analysis && (
            <div>
              <h4>Gap Analysis</h4>
              {contract.gap_analysis.missing_fields && contract.gap_analysis.missing_fields.length > 0 ? (
                <ul>
                  {contract.gap_analysis.missing_fields.map((field, index) => (
                    <li key={index}>{field}</li>
                  ))}
                </ul>
              ) : (
                <p>No missing fields identified.</p>
              )}
            </div>
          )}
          <a href={`http://localhost:8000/contracts/${contract.contract_id}/download`} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-block', marginTop: '20px', padding: '10px 15px', backgroundColor: '#28a745', color: 'white', textDecoration: 'none', borderRadius: '5px' }}>Download Original Contract</a>
        </div>
      ) : (
        <p>Contract processing is not yet completed or data is not available.</p>
      )}
    </div>
  );
}

export default ContractDetail;
