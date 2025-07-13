
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import io
import json
import os
import re
import requests # For making HTTP requests to the LLM API
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try importing PyPDF2 first, fall back to pypdf if PyPDF2 is not found
try:
    import PyPDF2
except ImportError:
    import pypdf as PyPDF2

app = FastAPI()

# Configure CORS to allow communication from the Streamlit frontend.
# In a production environment, you would restrict this to specific origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# In a real application, document content would be stored in a more persistent/scalable way,
# e.g., a database, object storage, or a vector store.
# For this demo, we'll keep it in memory for simplicity.
document_content_store = {} # Stores document content per session/user, keyed by a simple ID

# --- LLM API Configuration (Updated for Groq) ---
# Get API key from environment variables.
# IMPORTANT: You MUST set GROQ_API_KEY in your .env file.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions" # Groq's OpenAI-compatible endpoint
GROQ_MODEL_NAME = "llama3-8b-8192" # Or "mixtral-8x7b-32768", or "gemma-7b-it"

# --- Helper Function for LLM API Calls (Updated for Groq) ---
async def call_llm_api(prompt: str, response_schema: dict = None):
    """
    Makes a request to the LLM API (Groq) for text generation.
    Supports structured JSON responses if a schema is provided.
    """
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API Key is not set. Please check your .env file or environment variables.")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GROQ_API_KEY}'
    }

    # Groq uses an OpenAI-compatible chat completions format
    messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": GROQ_MODEL_NAME,
        "messages": messages,
        "temperature": 0.7, # You can adjust temperature
        "max_tokens": 1024, # Adjust max tokens as needed
        "response_format": {"type": "json_object"} if response_schema else {"type": "text"}
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()

        # Extract content from Groq's response structure
        if result.get("choices") and result["choices"][0].get("message") and \
           result["choices"][0]["message"].get("content"):
            text_response = result["choices"][0]["message"]["content"]

            if response_schema:
                try:
                    return json.loads(text_response)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from LLM: {text_response}")
                    raise HTTPException(status_code=500, detail="LLM response was not valid JSON.")
            return text_response
        else:
            print(f"Unexpected LLM response structure: {result}")
            raise HTTPException(status_code=500, detail="LLM did not return a valid response.")
    except requests.exceptions.RequestException as e:
        print(f"Network or API error calling LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to LLM service: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# --- Document Processing Endpoints (No Change) ---

@app.post("/upload_document")
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads a document (PDF or TXT), extracts its content, and stores it.
    """
    file_id = "user_document" # Simple ID for demo. In production, use session/user ID.
    extracted_text = ""

    try:
        if file.content_type == "text/plain":
            extracted_text = (await file.read()).decode("utf-8")
        elif file.content_type == "application/pdf":
            # Use PyPDF2 to read PDF content from bytes
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(await file.read()))
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                extracted_text += page.extract_text() + "\n"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF and TXT are supported.")

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the document. It might be a scanned PDF without text layer.")

        document_content_store[file_id] = extracted_text
        return JSONResponse(content={"message": f"File '{file.filename}' processed successfully.", "file_id": file_id})

    except Exception as e:
        print(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {e}")

# --- AI Interaction Endpoints (Prompts remain similar, API call function changes) ---

class DocumentRequest(BaseModel):
    file_id: str

class SummarizeRequest(DocumentRequest):
    pass

@app.post("/summarize")
async def summarize_document(request: SummarizeRequest):
    """
    Generates a concise summary of the uploaded document.
    """
    document_text = document_content_store.get(request.file_id)
    if not document_text:
        raise HTTPException(status_code=404, detail="Document not found. Please upload a document first.")

    # Truncate document content for LLM to manage token limits
    truncated_document = document_text[:8000]

    prompt = f"""Summarize the following document content in no more than 150 words. Focus on the main points and key takeaways.
    Document Content:
    {truncated_document}"""

    try:
        # Call the updated LLM API function
        summary = await call_llm_api(prompt)
        return JSONResponse(content={"summary": summary})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {e}")

class AskQuestionRequest(DocumentRequest):
    question: str

@app.post("/ask_question")
async def ask_question(request: AskQuestionRequest):
    """
    Answers a free-form question based on the document content, with justification.
    """
    document_text = document_content_store.get(request.file_id)
    if not document_text:
        raise HTTPException(status_code=404, detail="Document not found. Please upload a document first.")

    truncated_document = document_text[:8000]

    prompt = f"""Based on the following document content, answer the question accurately and concisely.
    After the answer, provide a brief justification from the document, citing the relevant section or paragraph if possible.
    Format your response as:
    Answer: [Your Answer]
    Justification: [Your Justification from the document, e.g., "This is supported by paragraph 3 of section 1..."]

    Document Content (excerpt):
    {truncated_document}

    Question: {request.question}"""

    try:
        # Call the updated LLM API function
        response_text = await call_llm_api(prompt)
        # Parse the response to separate answer and justification
        answer_match = re.search(r"Answer: ([\s\S]*?)(?=\nJustification:|$)", response_text, re.IGNORECASE)
        justification_match = re.search(r"Justification: ([\s\S]*)", response_text, re.IGNORECASE)

        answer = answer_match.group(1).strip() if answer_match else "Could not extract answer."
        justification = justification_match.group(1).strip() if justification_match else "No justification provided."

        return JSONResponse(content={"answer": answer, "justification": justification})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get answer: {e}")

@app.post("/generate_questions")
async def generate_questions(request: DocumentRequest):
    """
    Generates three logic-based or comprehension-focused questions from the document.
    """
    document_text = document_content_store.get(request.file_id)
    if not document_text:
        raise HTTPException(status_code=404, detail="Document not found. Please upload a document first.")

    truncated_document = document_text[:8000]

    prompt = f"""Generate three (3) distinct, logic-based or comprehension-focused questions derived from the following document.
    The questions should require understanding and inference, not just direct recall.
    Provide the questions in a JSON array format, where each object has a "question" key.
    Example: {{"questions": [{{"question": "What is the primary implication of X on Y?"}}, {{"question": "How does A relate to B in the context of C?"}}, {{"question": "Based on the text, what is a potential consequence of Z?"}}]}}

    Document Content (excerpt):
    {truncated_document}"""

    # JSON schema for the expected response format
    schema = {
        "type": "OBJECT",
        "properties": {
            "questions": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "question": {"type": "STRING"}
                    },
                    "required": ["question"]
                }
            }
        },
        "required": ["questions"]
    }

    try:
        # Call the updated LLM API function
        response_json = await call_llm_api(prompt, schema)
        if response_json and "questions" in response_json:
            return JSONResponse(content={"questions": response_json["questions"]})
        else:
            raise HTTPException(status_code=500, detail="LLM did not return questions in the expected format.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {e}")

class EvaluateAnswerRequest(BaseModel):
    file_id: str
    question: str
    user_answer: str

@app.post("/evaluate_answer")
async def evaluate_answer(request: EvaluateAnswerRequest):
    """
    Evaluates a user's answer to a generated question, with feedback and justification.
    """
    document_text = document_content_store.get(request.file_id)
    if not document_text:
        raise HTTPException(status_code=404, detail="Document not found. Please upload a document first.")

    truncated_document = document_text[:8000]

    prompt = f"""Evaluate the following user's answer to the question based on the provided document content.
    Provide feedback on correctness (e.g., "Correct", "Partially Correct", "Incorrect") and a brief justification from the document.
    Format your response as:
    Evaluation: [Feedback on correctness]
    Justification: [Your justification from the document, e.g., "This is supported by paragraph X of section Y..."]

    Document Content (excerpt):
    {truncated_document}

    Question: {request.question}
    User's Answer: {request.user_answer}"""

    try:
        # Call the updated LLM API function
        response_text = await call_llm_api(prompt)
        # Parse the response to separate evaluation and justification
        evaluation_match = re.search(r"Evaluation: ([\s\S]*?)(?=\nJustification:|$)", response_text, re.IGNORECASE)
        justification_match = re.search(r"Justification: ([\s\S]*)", response_text, re.IGNORECASE)

        evaluation = evaluation_match.group(1).strip() if evaluation_match else "No evaluation provided."
        justification = justification_match.group(1).strip() if justification_match else "No justification provided."

        return JSONResponse(content={"evaluation": evaluation, "justification": justification})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate answer: {e}")

# To run the FastAPI app directly (for local testing outside of a combined setup)
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)


