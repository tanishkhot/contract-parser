
from celery import Celery
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import time
import fitz  # PyMuPDF
from supabase import create_client, Client
import re
import groq
import json

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

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

groq_client = groq.Groq(api_key=GROQ_API_KEY)

celery_app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
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

        # 4. Extract data using Groq
        extracted_data = extract_contract_data_with_groq(text)

        # 5. Calculate the overall score
        overall_score = calculate_overall_score(extracted_data)

        # 6. Update the database with extracted data and score
        contracts_collection.update_one(
            {"_id": contract_id}, 
            {"$set": {"status": "completed", "extracted_data": extracted_data, "overall_score": overall_score, "text": text}}
        )

        return {"status": "completed", "contract_id": contract_id}
    except Exception as e:
        contracts_collection.update_one({"_id": contract_id}, {"$set": {"status": "failed", "error": str(e)}})
        return {"status": "failed", "contract_id": contract_id, "error": str(e)}

def extract_contract_data_with_groq(text):
    prompt = f"""You are an expert contract analysis AI. Your task is to read the following contract text and extract the key information in a structured JSON format.

    The JSON object should have the following structure. For each section, provide a confidence score from 0.0 to 1.0, where 1.0 is very confident and 0.0 is very uncertain.
    {{
      "party_identification": {{
        "parties": [
          {{
            "name": "...",
            "role": "customer/vendor/third-party",
            "registration_details": "..."
          }}
        ],
        "signatories": [
          {{
            "name": "...",
            "role": "..."
          }}
        ],
        "confidence_score": "Rate your confidence in the extracted party information on a scale of 0.0 to 1.0"
      }},
      "account_information": {{
        "billing_details": "...",
        "account_numbers": "...",
        "contact_information": {{
          "billing_contact": "...",
          "technical_contact": "..."
        }},
        "confidence_score": "Rate your confidence in the extracted account information on a scale of 0.0 to 1.0"
      }},
      "financial_details": {{
        "line_items": [
          {{
            "description": "...",
            "quantity": 0,
            "unit_price": 0.0
          }}
        ],
        "total_contract_value": "...",
        "currency": "...",
        "tax_information": "...",
        "additional_fees": "...",
        "confidence_score": "Rate your confidence in the extracted financial details on a scale of 0.0 to 1.0"
      }},
      "payment_structure": {{
        "payment_terms": "...",
        "payment_schedule": "...",
        "payment_methods": "...",
        "confidence_score": "Rate your confidence in the extracted payment structure on a scale of 0.0 to 1.0"
      }},
      "revenue_classification": {{
        "recurring_vs_one_time": "...",
        "subscription_model": "...",
        "renewal_terms": "...",
        "confidence_score": "Rate your confidence in the extracted revenue classification on a scale of 0.0 to 1.0"
      }},
      "service_level_agreements": {{
        "performance_metrics": "...",
        "penalty_clauses": "...",
        "support_and_maintenance_terms": "...",
        "confidence_score": "Rate your confidence in the extracted service level agreements on a scale of 0.0 to 1.0"
      }}
    }}

    Here is the contract text:
    ---
    {text}
    ---
    """


    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gemma2-9b-it",
        response_format={"type": "json_object"}
    )

    return json.loads(chat_completion.choices[0].message.content)

def calculate_overall_score(extracted_data):
    # Weighted Scoring System (0-100 points)
    # - Financial completeness: 30 points
    # - Party identification: 25 points
    # - Payment terms clarity: 20 points
    # - SLA definition: 15 points
    # - Contact information: 10 points

    weights = {
        "party_identification": 25,
        "financial_details": 30,
        "payment_structure": 20,
        "service_level_agreements": 15,
        "account_information": 10
    }

    total_score = 0
    for key, weight in weights.items():
        if key in extracted_data and "confidence_score" in extracted_data[key]:
            try:
                confidence = float(extracted_data[key]["confidence_score"])
                total_score += confidence * weight
            except (ValueError, TypeError):
                # Handle cases where the confidence score is not a valid number
                pass

    return total_score
