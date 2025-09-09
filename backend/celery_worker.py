
from celery import Celery
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import time
import fitz  # PyMuPDF
from supabase import create_client, Client
import re

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or Key not set in environment variables")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "Contracts"

celery_app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

client = MongoClient(MONGO_URI)
db = client.contract_db
contracts_collection = db.contracts

@celery_app.task
def process_contract(contract_id):
    # Update status to processing
    contracts_collection.update_one({"_id": contract_id}, {"$set": {"status": "processing"}})

    try:
        # 1. Retrieve contract metadata from MongoDB
        contract = contracts_collection.find_one({"_id": contract_id})
        if not contract:
            raise Exception("Contract not found")

        supabase_path = contract.get("supabase_path")
        if not supabase_path:
            raise Exception("File path not found for this contract")

        # 2. Download the file from Supabase Storage
        pdf_content = supabase.storage.from_(BUCKET_NAME).download(supabase_path)

        # 3. Extract text from the PDF
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        # 4. Extract data using regular expressions
        party_names = extract_party_names(text)
        total_value = extract_total_value(text)

        # 5. Update the database with extracted data
        extracted_data = {
            "party_names": party_names,
            "total_contract_value": total_value
        }
        contracts_collection.update_one(
            {"_id": contract_id}, 
            {"$set": {"status": "completed", "extracted_data": extracted_data, "text": text}}
        )

        return {"status": "completed", "contract_id": contract_id}
    except Exception as e:
        contracts_collection.update_one({"_id": contract_id}, {"$set": {"status": "failed", "error": str(e)}})
        return {"status": "failed", "contract_id": contract_id, "error": str(e)}

def extract_party_names(text):
    # This is a very basic example. A more robust solution would use NLP techniques.
    party_pattern = re.compile(r"(?:between|among)\s+(.*?)\s+(?:and|&)\s+(.*?)(?:\n|\r|,)", re.IGNORECASE | re.DOTALL)
    matches = party_pattern.findall(text)
    parties = []
    for match in matches:
        parties.extend([p.strip() for p in match])
    return parties

def extract_total_value(text):
    # This is a very basic example. A more robust solution would handle different currencies and formats.
    value_pattern = re.compile(r"total\s+contract\s+value\s*[:\-]?\s*\$?([\d,]+\.?\d*)", re.IGNORECASE)
    match = value_pattern.search(text)
    if match:
        return match.group(1)
    return None
