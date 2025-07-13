# **AI Document Assistant**

## **Table of Contents**

1. [About the Project](https://www.google.com/search?q=%23about-the-project)  
2. [Features](https://www.google.com/search?q=%23features)  
3. [Architecture](https://www.google.com/search?q=%23architecture)  
4. [Technologies Used](https://www.google.com/search?q=%23technologies-used)  
5. [Installation](https://www.google.com/search?q=%23installation)  
   * [Prerequisites](https://www.google.com/search?q=%23prerequisites)  
   * [Backend Setup](https://www.google.com/search?q=%23backend-setup)  
   * [Frontend Setup](https://www.google.com/search?q=%23frontend-setup)  
6. [Usage](https://www.google.com/search?q=%23usage)

## **1\. About the Project**

The AI Document Assistant is an interactive platform designed to streamline document processing and analysis. It allows users to upload PDF or TXT documents and interact with them using AI-powered functionalities such as summarization, contextual question-answering, and a "Challenge Me" mode for logic-based question generation and evaluation. The primary objective is to automate complex document-related tasks, thereby enhancing efficiency and accessibility of information.

## **2\. Features**

* **Document Upload:** Upload PDF or TXT files for processing.  
* **Automatic Summarization:** Get a concise summary of the uploaded document.  
* **Ask Anything Mode:** Ask free-form questions about the document and receive accurate answers with justifications.  
* **Challenge Me Mode:** Generate logic-based or comprehension-focused questions from the document and evaluate your answers against the document's content.

## **3\. Architecture**

The AI Document Assistant employs a bifurcated architecture, separating the user interface from the core business logic:

* **Frontend (app.py):** Built with Streamlit, this component provides the graphical user interface, handles user inputs, and displays results. It acts purely as a presentation layer, making API calls to the backend.  
* **Backend (main.py):** Powered by FastAPI, this component handles the core business logic, including:  
  * Document content extraction (PDF/TXT).  
  * Orchestration of AI model interactions (via Groq API).  
  * Generating summaries, answers, questions, and evaluations.  
  * Exposing a set of RESTful APIs consumed by the frontend.

This separation ensures decoupling, allowing independent development, scaling, and maintenance of both the UI and the underlying computational services.

## **4\. Technologies Used**

* **Frontend:**  
  * [Streamlit](https://streamlit.io/): For building interactive web applications in Python.  
* **Backend:**  
  * [FastAPI](https://fastapi.tiangolo.com/): A modern, fast (high-performance) web framework for building APIs with Python 3.7+.  
  * [Uvicorn](https://www.uvicorn.org/): An ASGI server for running FastAPI applications.  
  * [PyPDF2](https://pypdf2.readthedocs.io/en/3.0.0/) (or pypdf): For PDF text extraction.  
  * [Requests](https://requests.readthedocs.io/en/latest/): For making HTTP requests to external APIs.  
  * [Pydantic](https://pydantic-docs.helpmanual.io/): For data validation and settings management.  
  * [python-dotenv](https://pypi.org/project/python-dotenv/): For loading environment variables from a .env file.  
* **AI Model:**  
  * [Groq API](https://groq.com/): Utilized for fast inference with large language models (e.g., Llama3-8b-8192).

## **5\. Installation**

Follow these steps to set up the AI Document Assistant locally.

### **Prerequisites**

* Python 3.8+  
* pip (Python package installer)

### **Backend Setup**

1. **Clone the repository (if applicable):**  
   git clone \<https://github.com/anshukumar172/Smart-Assistant-for-Research-Summarization.git>  
   cd \<repository\_name\>

2. Create a virtual environment:  
   It's highly recommended to use a virtual environment to manage project dependencies.  
   python \-m venv venv

3. **Activate the virtual environment:**  
   * **On macOS/Linux:**  
     source venv/bin/activate

   * **On Windows:**  
     .\\venv\\Scripts\\activate

4. **Install backend dependencies:**  
   pip install \-r requirements.txt

   *(Note: Ensure you have a requirements.txt file in your project root containing fastapi, uvicorn, pypdf2 (or pypdf), python-dotenv, requests, pydantic.)*  
5. Configure Environment Variables:  
   Create a .env file in the root directory of your project (where main.py is located) and add your Groq API key:  
   GROQ\_API\_KEY="your\_groq\_api\_key\_here"

   Replace "your\_groq\_api\_key\_here" with your actual API key obtained from [Groq](https://console.groq.com/keys).  
6. **Run the FastAPI backend:**  
   uvicorn main:app \--reload \--host 0.0.0.0 \--port 8000

   The backend will typically run on http://localhost:8000.

### **Frontend Setup**

The frontend uses the same virtual environment and dependencies.

1. **Ensure your virtual environment is active** (as per step 3 in Backend Setup).  
2. **Run the Streamlit frontend:**  
   streamlit run app.py

   This will open the Streamlit application in your web browser, usually at http://localhost:8501.

## **6\. Usage**

1. **Upload Document:** On the main page, use the "Choose a PDF or TXT file" button to upload your document. The system will automatically generate a summary after upload.  
2. **Choose Interaction Mode:**  
   * **Ask Anything:** Enter any question related to the document in the text area and click "Get Answer" to receive a direct answer and justification.  
   * **Challenge Me:** Click "Generate Questions" to get a set of logic-based questions. Provide your answers in the respective text areas and click "Submit Answers" to see the evaluation and justification for each.