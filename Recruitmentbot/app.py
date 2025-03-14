import autogen
import pdfplumber
import re
import os
from flask import Flask, request, jsonify, render_template

# === Flask App Initialization ===
app = Flask(__name__)

# === Helper Function: Extract Text from PDF ===
def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# === Agent 1: Resume Parser ===
resume_parser = autogen.AssistantAgent(
    name="resume_parser",
    system_message="You extract structured information (name, skills, experience) from resumes."
)

# === Agent 2: Job Matcher ===
job_matcher = autogen.AssistantAgent(
    name="job_matcher",
    system_message="Compare candidate skills with job descriptions and return a compatibility score (0-100%)."
)

# === Agent 3: Scheduler ===
scheduler_agent = autogen.AssistantAgent(
    name="scheduler_agent",
    system_message="Schedule an interview with the candidate via email."
)

# === Main Workflow Function ===
def recruitment_workflow(resume_path, job_description):
    resume_text = extract_text_from_pdf(resume_path)

    # Step 1: Parse Resume
    resume_response = resume_parser.initiate_chat(
        job_matcher,
        message=f"Extract name, skills, education, and work experience from the following resume: {resume_text}"
    )

    resume_text_parsed = resume_response.outputs[-1]  # Get the last output message

    # Step 2: Match Candidate to Job
    match_response = job_matcher.initiate_chat(
        resume_parser,
        message=f"Compare this candidate profile: {resume_text_parsed} to the job description: {job_description}.\nReturn a match score and reasons."
    )

    match_text = match_response.outputs[-1]  # Get last output message

    # Extract match score
    match_score = 0
    match_score_match = re.search(r"(\d+)%", match_text)
    if match_score_match:
        match_score = int(match_score_match.group(1))

    # Step 3: Schedule Interview (if match > 70%)
    if match_score >= 70:
        scheduler_agent.initiate_chat(
            job_matcher,
            message="Schedule an interview for this candidate with the hiring manager."
        )
        return {
            "status": "Interview Scheduled",
            "resume_info": resume_text_parsed,
            "match_score": match_score
        }
    else:
        return {
            "status": "Candidate Not Suitable",
            "resume_info": resume_text_parsed,
            "match_score": match_score
        }

# === Home Page: Upload Form ===
@app.route('/', methods=['GET'])
def index():
    return '''
    <!doctype html>
    <html lang="en">
    <head>
        <title>AI Recruitment Assistant</title>
    </head>
    <body>
        <h1>Upload Resume and Job Description</h1>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <label for="resume">Upload Resume (PDF):</label>
            <input type="file" name="resume" accept="application/pdf" required><br><br>

            <label for="job_description">Job Description:</label><br>
            <textarea name="job_description" rows="5" cols="50" required></textarea><br><br>

            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    '''

# === API Endpoint: Upload Resume and Job Description ===
@app.route('/upload', methods=['POST'])
def upload():
    if 'resume' not in request.files or 'job_description' not in request.form:
        return jsonify({"error": "Missing resume or job description"}), 400

    resume = request.files['resume']
    job_description = request.form['job_description']

    resume_path = os.path.join("uploads", resume.filename)
    os.makedirs("uploads", exist_ok=True)
    resume.save(resume_path)

    result = recruitment_workflow(resume_path, job_description)

    return jsonify(result)

# === Run Flask Application ===
if __name__ == '__main__':
    app.run(debug=True, port=5000)
