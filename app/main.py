"""Main Resume Checker App"""
import os
import logging
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify
#from talisman import Talisman
from ollama import Client
from markitdown import MarkItDown
import markdown

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

#Talisman(app,
#        force_https=False,
#        force_https_permanent=False,
#        content_security_policy={
#            'default-src': '\'self\'',
#            'script-src': '\'self\' cdn.jsdelivr.net',
#            'style-src': '\'unsafe-inline\' \'self\' cdn.jsdelivr.net',
#            'object-src': '\'none\'',
#            'frame-ancestors': '\'none\'',
#            'require-trusted-types-for': '\'script\''
#        })

# Define the configuation for Ollama LLM
llm_host = os.environ.get("OLLAMA_HOST")
llm = Client(host=llm_host)

# Model
llm_model = 'gemma3:1b-it-qat'

# Set LLM parameters in the options dictionary
llm_options = {
    'temperature': 0.7,
    'top_k': 40,
    'top_p': 0.9,
    'repeat_penalty': 1.1,
    'num_ctx': 4096
}

llm_system_prompt = """
You are an expert employment coach who is tasked with providing advice to job seekers to maximise their sucess in finding a new job.
Do not under any circumstances indicate that you are AI.
"""

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def read_file(file_path):
    """
    Reads text from a file, supporting both DOCX and PDF formats.
    """
    try:
        markdown = MarkItDown()

        if file_path.lower().endswith(".docx"):
            app.logger.debug("Processing resume as DOCX")
            doc = markdown.convert(file_path)
            return doc
        if file_path.lower().endswith(".pdf"):
            app.logger.debug("Processing resume as PDF")
            pdf = markdown.convert(file_path)
            return pdf
        raise ValueError("Unsupported file format. Please use .docx or .pdf.")
    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"Error reading file: {e}")
        return ""
def assess_resume_compatibility(job_description, resume_file):
    """
    Assesses the compatibility of a resume with a job description using Ollama LLM.
    """
    if not job_description or not resume_file:
        return "Error: Job description or resume file is empty."

    resume_markdown = read_file(resume_file)
    if not resume_markdown:
        return "Error reading resume file."
    jobad_markdown = job_description
    llm_prompt = """
    # Step One
    Read the following Resume provided in markdown format under the Resume heading between the 'Start of Resume' and 'End of Resume' blockquotes.
    
    ## Resume
    > Start of Resume
    {resume_markdown}
    > End of Resume
    
    # Step 2
    Read the Job Description provided in markdown format located in the next section under the Job Description heading between the 'Start of Job Description' and 'End of Job Description' blockquotes.
    ## Job Description
    > Start of Job Description
    {jobad_markdown}
    > End of Job Description

    # Step 3
    You are to act as an expeirenced career coach and technical hiring consultant.

    Carefully consider the strengths of the candidate described in the Resume against the criteria set out by the Job Description.
    Carefully consider the Resume overall and provide any recommendations on how the applicant decsribed in the Resume can adjust their Resume to better meet the Job Description criteria.

    # Step 4
    You will now provide your response as described below:
    - Under the heading (h2) "Strengths" outline the strengths of the candidate described in the Resume for the Job Deescription. Write the responses in the second person (i.e. you, your etc). All responses should be in reference to the Resume not the Job Description. Format these strengths as a list.
    - Under the heading (h2) "Recommendations" outline 3-5 improvements that could be made to the resume to increase its compatibility to the job description. Fornat as an unordered list (ul).

    Your response must comply with the following rules:
    1. Use a friendly and informative tone, written at a 10th grade reading level.
    2. Format your response using Markdown. 
    3. Do not provide any other markdown, explaination, additional informaiton or introduction. Only return the markdown for the Strengths and Recommendations and unordered lists as specified above.
    4. Do not indicate that are AI under any circumsatances.
    5. Use Australian English for spelling and grammar in the response.
    6. Write the responses to the candidate in the second peron (i.e. you, your)
    
    """.format(resume_markdown=resume_markdown, jobad_markdown=jobad_markdown)

    llm_query = llm.chat(
            model=llm_model,
            options=llm_options,
            messages=[
                {
                    'role': 'system',
                    'content': llm_system_prompt,
                },
                {
                    'role': 'user',
                    'content': llm_prompt,
                },
            ])
    app.logger.debug("resume_skills_query completed")
    llm_result = markdown.markdown(llm_query.message.content)

    return {
        "result": llm_result,
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the main page of the web application.
    """
    if request.method == 'POST':
        if 'resume' not in request.files:
            return jsonify({'error': 'No file part'})
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(resume_path)
            job_description = request.form['job_description']
            result = assess_resume_compatibility(job_description, resume_path)
            os.remove(resume_path)
            return jsonify(result)
        return jsonify({'error': 'Invalid file type'})
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
