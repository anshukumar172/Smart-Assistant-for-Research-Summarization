# app.py
# This file sets up the Streamlit frontend for the AI Document Assistant.
# It provides the user interface for uploading documents, displaying summaries,
# asking questions, and engaging in the "Challenge Me" mode.
# It communicates with the FastAPI backend to perform AI-powered operations.

import streamlit as st
import requests
import json
import time

# --- Configuration ---
BACKEND_URL = "http://localhost:8000" # URL of your FastAPI backend

# --- Streamlit UI Setup ---
st.set_page_config(
    page_title="AI Document Assistant",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("AI Document Assistant")
st.markdown("Upload a document (PDF or TXT) and interact with it using AI.")

# --- Session State Initialization ---
# Use st.session_state to persist data across Streamlit reruns
if 'document_content' not in st.session_state:
    st.session_state.document_content = None
if 'file_id' not in st.session_state:
    st.session_state.file_id = None
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'interaction_mode' not in st.session_state:
    st.session_state.interaction_mode = None # 'ask_anything' or 'challenge_me'
if 'generated_questions' not in st.session_state:
    st.session_state.generated_questions = []
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = []

# --- Document Upload Section ---
st.header("1. Upload Document (PDF/TXT)")
uploaded_file = st.file_uploader("Choose a PDF or TXT file", type=["pdf", "txt"])

if uploaded_file is not None and st.session_state.document_content is None:
    with st.spinner("Processing document... This may take a moment."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        try:
            response = requests.post(f"{BACKEND_URL}/upload_document", files=files)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            result = response.json()
            st.session_state.file_id = result.get("file_id")
            st.session_state.document_content = "Document uploaded and processed." # Placeholder, content is on backend
            st.success(result.get("message", "Document uploaded successfully!"))

            # Automatically generate summary after upload
            with st.spinner("Generating summary..."):
                summary_response = requests.post(f"{BACKEND_URL}/summarize", json={"file_id": st.session_state.file_id})
                summary_response.raise_for_status()
                st.session_state.summary = summary_response.json().get("summary", "Could not generate summary.")
                st.session_state.interaction_mode = None # Reset mode after new upload
                st.session_state.generated_questions = [] # Clear old questions
                st.session_state.user_answers = {}
                st.session_state.evaluation_results = []

        except requests.exceptions.RequestException as e:
            st.error(f"Error uploading or processing file: {e}")
            st.session_state.document_content = None # Reset if error
            st.session_state.file_id = None
        except json.JSONDecodeError:
            st.error("Received invalid JSON response from backend.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

# --- Document Summary Section ---
if st.session_state.document_content:
    st.header("2. Document Summary")
    if st.session_state.summary:
        st.info(st.session_state.summary)
    else:
        st.warning("Summary not available. Please upload a document.")

# --- Interaction Modes Section ---
if st.session_state.document_content:
    st.header("3. Choose Interaction Mode")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ask Anything", key="ask_mode_btn"):
            st.session_state.interaction_mode = 'ask_anything'
            st.session_state.generated_questions = [] # Clear challenge mode data
            st.session_state.user_answers = {}
            st.session_state.evaluation_results = []
    with col2:
        if st.button("Challenge Me", key="challenge_mode_btn"):
            st.session_state.interaction_mode = 'challenge_me'
            st.session_state.generated_questions = [] # Clear previous questions
            st.session_state.user_answers = {}
            st.session_state.evaluation_results = []

# --- Ask Anything Mode ---
if st.session_state.interaction_mode == 'ask_anything':
    st.header("Ask Anything (Contextual Understanding)")
    question = st.text_area("Your Question:", key="ask_question_input", height=100)
    if st.button("Get Answer", key="submit_ask_question_btn"):
        if st.session_state.file_id and question:
            with st.spinner("Generating answer..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/ask_question",
                        json={"file_id": st.session_state.file_id, "question": question}
                    )
                    response.raise_for_status()
                    result = response.json()
                    st.subheader("Answer:")
                    st.write(result.get("answer", "No answer found."))
                    st.subheader("Justification:")
                    st.markdown(f"*{result.get('justification', 'No justification provided.')}*")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error getting answer: {e}")
                except json.JSONDecodeError:
                    st.error("Received invalid JSON response from backend.")
        else:
            st.warning("Please upload a document and enter a question.")

# --- Challenge Me Mode ---
elif st.session_state.interaction_mode == 'challenge_me':
    st.header("Challenge Me (Logic-Based Question Generation)")

    if st.button("Generate Questions", key="generate_questions_btn"):
        if st.session_state.file_id:
            with st.spinner("Generating questions..."):
                try:
                    response = requests.post(f"{BACKEND_URL}/generate_questions", json={"file_id": st.session_state.file_id})
                    response.raise_for_status()
                    result = response.json()
                    st.session_state.generated_questions = result.get("questions", [])
                    st.session_state.user_answers = {str(i): "" for i in range(len(st.session_state.generated_questions))}
                    st.session_state.evaluation_results = [] # Clear previous evaluations
                except requests.exceptions.RequestException as e:
                    st.error(f"Error generating questions: {e}")
                except json.JSONDecodeError:
                    st.error("Received invalid JSON response from backend.")
        else:
            st.warning("Please upload a document first.")

    if st.session_state.generated_questions:
        st.subheader("Your Challenge:")
        for i, q_obj in enumerate(st.session_state.generated_questions):
            question_text = q_obj.get("question", f"Question {i+1} not found.")
            st.write(f"**Question {i+1}:** {question_text}")
            user_answer = st.text_area(f"Your answer for Question {i+1}:",
                                       value=st.session_state.user_answers.get(str(i), ""),
                                       key=f"user_answer_{i}",
                                       height=80)
            st.session_state.user_answers[str(i)] = user_answer # Update session state on change

        if st.button("Submit Answers", key="submit_challenge_answers_btn"):
            if st.session_state.file_id:
                st.session_state.evaluation_results = [] # Clear before re-evaluating
                with st.spinner("Evaluating your answers..."):
                    for i, q_obj in enumerate(st.session_state.generated_questions):
                        question_text = q_obj.get("question")
                        user_answer = st.session_state.user_answers.get(str(i), "")

                        if not user_answer.strip():
                            st.session_state.evaluation_results.append({
                                "question": question_text,
                                "user_answer": user_answer,
                                "evaluation": "No answer provided.",
                                "justification": "Please provide an answer to be evaluated."
                            })
                            continue # Skip to next question

                        try:
                            response = requests.post(
                                f"{BACKEND_URL}/evaluate_answer",
                                json={
                                    "file_id": st.session_state.file_id,
                                    "question": question_text,
                                    "user_answer": user_answer
                                }
                            )
                            response.raise_for_status()
                            result = response.json()
                            st.session_state.evaluation_results.append({
                                "question": question_text,
                                "user_answer": user_answer,
                                "evaluation": result.get("evaluation", "Could not evaluate."),
                                "justification": result.get("justification", "No justification provided.")
                            })
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error evaluating answer for Q{i+1}: {e}")
                            st.session_state.evaluation_results.append({
                                "question": question_text,
                                "user_answer": user_answer,
                                "evaluation": "Error during evaluation.",
                                "justification": str(e)
                            })
                        except json.JSONDecodeError:
                            st.error(f"Invalid JSON response for Q{i+1} evaluation.")
                            st.session_state.evaluation_results.append({
                                "question": question_text,
                                "user_answer": user_answer,
                                "evaluation": "Error: Invalid response.",
                                "justification": "Backend returned invalid JSON."
                            })
            else:
                st.warning("Please upload a document first.")
            st.rerun() # Changed from st.experimental_rerun()

        # Display Evaluation Results
        if st.session_state.evaluation_results:
            st.subheader("Evaluation Results:")
            for i, eval_data in enumerate(st.session_state.evaluation_results):
                st.markdown(f"---")
                st.markdown(f"**Question {i+1}:** {eval_data['question']}")
                st.markdown(f"**Your Answer:** *{eval_data['user_answer']}*")

                # Apply color based on evaluation
                eval_text = eval_data['evaluation'].lower()
                if "correct" in eval_text and "partially" not in eval_text:
                    st.success(f"**Evaluation:** {eval_data['evaluation']}")
                elif "partially correct" in eval_text:
                    st.warning(f"**Evaluation:** {eval_data['evaluation']}")
                elif "incorrect" in eval_text or "no answer" in eval_text or "error" in eval_text:
                    st.error(f"**Evaluation:** {eval_data['evaluation']}")
                else:
                    st.info(f"**Evaluation:** {eval_data['evaluation']}")

                st.markdown(f"**Justification:** *{eval_data['justification']}*")