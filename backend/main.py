
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import io
import uuid
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from supabase import create_client, Client # Import the Supabase client
from datetime import datetime

from celery_worker import process_contract

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# --- MongoDB Setup ---
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set")
client = MongoClient(MONGO_URI)
db = client.contract_db
contracts_collection = db.contracts

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or Key not set in environment variables")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "Contracts"

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/contracts/upload")
async def upload_contract(file: UploadFile = File(...)):
    contract_id = str(uuid.uuid4())
    # Create a unique path/filename for the object in the bucket
    object_path = f"contracts/{contract_id}-{file.filename}" 
    
    # Read the PDF content
    pdf_content = await file.read()

    # 1. Upload the file to Supabase Storage
    try:
        supabase.storage.from_(BUCKET_NAME).upload(
            file=pdf_content,
            path=object_path,
            file_options={"content-type": file.content_type}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to Supabase: {str(e)}")

    # 2. Store the metadata in MongoDB
    try:
        contract_data = {
            "_id": contract_id,
            "filename": file.filename,
            "supabase_path": object_path, # Store the path to the file in Supabase
            "status": "pending",
            "upload_time": datetime.utcnow()
        }
        contracts_collection.insert_one(contract_data)
    except Exception as e:
        # If storing metadata fails, delete the file from Supabase to clean up
        supabase.storage.from_(BUCKET_NAME).remove([object_path])
        raise HTTPException(status_code=500, detail=f"Failed to store contract metadata in MongoDB: {e}")
    
    # Trigger the background processing task
    process_contract.delay(contract_id)

    return {"contract_id": contract_id, "message": "Contract uploaded and queued for processing"}

@app.get("/contracts")
async def get_contracts():
    try:
        # Retrieve all contracts from the collection
        all_contracts = list(contracts_collection.find({}, {"_id": 1, "filename": 1, "status": 1, "upload_time": 1}))
        
        # Convert ObjectId to string for JSON serialization
        for contract in all_contracts:
            contract["_id"] = str(contract["_id"])
            
        return all_contracts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve contracts from MongoDB: {e}")

@app.get("/contracts/{contract_id}/status")
async def get_contract_status(contract_id: str):
    try:
        contract = contracts_collection.find_one({"_id": contract_id}, {"status": 1})
        if contract:
            return {"status": contract.get("status")}
        else:
            raise HTTPException(status_code=404, detail="Contract not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve contract status: {e}")

@app.get("/contracts/{contract_id}")
async def get_contract_data(contract_id: str):
    try:
        contract = contracts_collection.find_one({"_id": contract_id})
        if contract:
            # TODO: Add data extraction logic here
            # For now, just return the stored data
            contract["_id"] = str(contract["_id"])
            return contract
        else:
            raise HTTPException(status_code=404, detail="Contract not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve contract data: {e}")

@app.get("/contracts/{contract_id}/download")
async def download_contract(contract_id: str):
    try:
        # 1. Retrieve contract metadata from MongoDB
        contract = contracts_collection.find_one({"_id": contract_id})
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        supabase_path = contract.get("supabase_path")
        if not supabase_path:
            raise HTTPException(status_code=404, detail="File path not found for this contract")

        # 2. Download the file from Supabase Storage
        response = supabase.storage.from_(BUCKET_NAME).download(supabase_path)
        
        # 3. Return the file as a streaming response
        return StreamingResponse(io.BytesIO(response), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={contract.get('filename')}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download contract: {e}")