
from fastapi import FastAPI, UploadFile, File, HTTPException
import uuid
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from supabase import create_client, Client # Import the Supabase client
from datetime import datetime

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
    
    return {"contract_id": contract_id, "message": "Contract uploaded and stored in Supabase"}