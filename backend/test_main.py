import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
import mongomock

client = TestClient(app)

@pytest.fixture
def mock_collection():
    return mongomock.MongoClient().db.collection

@patch("main.contracts_collection")
@patch("main.supabase")
@patch("main.process_contract.delay")
def test_upload_contract(mock_delay, mock_supabase, mock_contracts_collection, mock_collection):
    mock_contracts_collection.return_value = mock_collection
    mock_supabase.storage.from_().upload.return_value = None

    file_content = b"test pdf content"
    with open("test.pdf", "wb") as f:
        f.write(file_content)

    with open("test.pdf", "rb") as f:
        response = client.post("/contracts/upload", files={"file": ("test.pdf", f, "application/pdf")})

    assert response.status_code == 200
    assert "contract_id" in response.json()
    assert response.json()["message"] == "Contract uploaded and queued for processing"
    mock_delay.assert_called_once()

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

@patch("main.contracts_collection")
def test_get_contracts(mock_contracts_collection, mock_collection):
    mock_contracts_collection.find.return_value = [
        {"_id": "1", "filename": "test1.pdf", "status": "pending"},
        {"_id": "2", "filename": "test2.pdf", "status": "completed"}
    ]

    response = client.get("/contracts")

    assert response.status_code == 200
    assert len(response.json()) == 2

@patch("main.contracts_collection")
def test_get_contract_status(mock_contracts_collection, mock_collection):
    mock_contracts_collection.find_one.return_value = {"status": "pending"}

    response = client.get("/contracts/1/status")

    assert response.status_code == 200
    assert response.json() == {"status": "pending"}

@patch("main.contracts_collection")
def test_get_contract_data(mock_contracts_collection, mock_collection):
    mock_contracts_collection.find_one.return_value = {"_id": "1", "filename": "test.pdf", "status": "completed", "extracted_data": {"party_names": ["A", "B"]}}

    response = client.get("/contracts/1")

    assert response.status_code == 200
    assert response.json()["filename"] == "test.pdf"
    assert response.json()["extracted_data"]["party_names"] == ["A", "B"]
