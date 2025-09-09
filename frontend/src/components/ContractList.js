import React from 'react';
import { Link } from 'react-router-dom'; // Import Link

function ContractList({ contracts }) {
  console.log('ContractList received contracts:', contracts); // <--- RE-ADDED LINE

  return (
    <div style={{ marginTop: '30px' }}>
      <h2>Contract List</h2>
      {contracts.length === 0 ? (
        <p>No contracts uploaded yet.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', margin: '20px 0' }}>
          <thead>
            <tr style={{ backgroundColor: '#f2f2f2' }}>
              <th style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'left' }}>Contract ID</th>
              <th style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'left' }}>Status</th>
              <th style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'left' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {contracts.map((contract) => (
              <tr key={contract.contract_id}>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>{contract.contract_id}</td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>{contract.status}</td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                  <Link to={`/contracts/${contract.contract_id}`} style={{ marginRight: '10px' }}>View Details</Link>
                  {contract.status === 'completed' && (
                    <a href={`http://localhost:8000/contracts/${contract.contract_id}/download`} target="_blank" rel="noopener noreferrer" style={{ marginRight: '10px' }}>Download</a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default ContractList;
