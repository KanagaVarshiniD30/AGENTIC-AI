import streamlit as st
import autogen
import pdfplumber
import os

def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])

def recruitment_workflow(resume_path, job_description):
    # Load and extract resume text
    resume_text = extract_text_from_pdf(resume_path)

    # Validate config.json path
    config_path = "config.json"
    if not os.path.exists(config_path):
        return "Error: config.json not found. Ensure the config file exists."

    # Initialize AutoGen agents
    try:
        config_list = autogen.config_list_from_json(config_path)
    except Exception as e:
        return f"Error loading config: {e}"

    resume_parser_agent = autogen.AssistantAgent("ResumeParser", config_list=config_list)
    user_proxy = autogen.UserProxyAgent("User", code_execution_config={"work_dir": "./"})

    # Run parsing
    try:
        resume_response = user_proxy.initiate_chat(
            resume_parser_agent,
            message=f"Extract key details from the following resume: {resume_text}\nJob Description: {job_description}"
        )

        resume_text_parsed = resume_response.message.content if resume_response.message else "No output received."
    except Exception as e:
        resume_text_parsed = f"Error processing resume: {e}"

    return resume_text_parsed

def main():
    st.title("AI Recruitment Assistant")

    # File upload
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    # Job description input
    job_description = st.text_area("Enter Job Description")

    if uploaded_file and st.button("Submit"):
        # Save uploaded file
        save_path = os.path.join("uploads", uploaded_file.name)
        os.makedirs("uploads", exist_ok=True)  # Ensure directory exists
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"File uploaded: {save_path}")

        # Run recruitment workflow
        result = recruitment_workflow(save_path, job_description)

        # Display output
        st.subheader("Parsed Resume Information")
        st.write(result)

if __name__ == "__main__":
    main()
