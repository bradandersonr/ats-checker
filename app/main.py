"""Main Resume Checker App"""
import os
import logging
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify
#from talisman import Talisman
from ollama import Client
from markitdown import MarkItDown

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
    llm_skills_prompt = """
    Review the following resume provided in markdown format located between the '# Start of Resume' and '# End of Resume' lines. 
    # Start of Resume
    {resume_markdown}
    # End of Resume

    Identify all of the professional skills listed in the resume.
    Return a comma seperated list containing the skills you have extracted from the resume.
    Remove any duplicate skills from the final list.
    Do not indicate the number of years of experience or any other information about the skill.
    Do not return any other comments, information or text apart from a single comma seperated list as described above.
    """.format(resume_markdown=resume_markdown)

    llm_jobad_prompt = """
    Read the following job advertisement.
    #Start of Job Ad
    {jobad_markdown}
    #End of Job Ad

    Identify all of the professional skills listed in the job ad.
    Return a comma seperated list containing the skills you have extracted from the job ad.
    Remove any duplicate skills from the final list.
    Do not return any other comments, information or text apart from a single comma seperated list as described above.
    """.format(jobad_markdown=jobad_markdown)
    app.logger.debug("Sending resume_skills_query to LLM")

    resume_skills_query = llm.chat(
            model=llm_model,
            options=llm_options,
            messages=[
                {
                    'role': 'system',
                    'content': llm_system_prompt,
                },
                {
                    'role': 'user',
                    'content': llm_skills_prompt,
                },
            ])
    app.logger.debug("resume_skills_query completed")
    resume_skills = resume_skills_query.message.content
    app.logger.debug("Sending jobad_skills_query to LLM")
    jobad_skills_query = llm.chat(
        model='gemma3:1b-it-qat',
        options=llm_options,
        messages=[
            {
                'role': 'system',
                'content': llm_system_prompt,
            },
            {
                'role': 'user',
                'content': llm_jobad_prompt,
            },
        ])
    app.logger.debug("jobad_skills_query completed")
    jobad_skills = jobad_skills_query.message.content
    llm_compatibility_prompt = """
    Read the list of skills contained in the canidates resume (comma seperated list)
    {resume_skills}

    Read the list of skills contained in the job ad (comma seperated list):
    {jobad_skills}

    Compare the two lists of skills and provide a comptaibility rating (integer out of 100) that indicates the percentage of similarilty between the similarity jobad and the resume.
    Do not return any other information or text. Only return an integer.
    """.format(resume_skills=resume_skills, jobad_skills=jobad_skills)
    app.logger.debug("Sednding compatability_query to LLM")
    compatability_query = llm.chat(
            model=llm_model,
            options=llm_options,
            messages=[
                {
                    'role': 'system',
                    'content': llm_system_prompt,
                },
                {
                    'role': 'user',
                    'content': llm_compatibility_prompt,
                },
            ])
    app.logger.debug("compatibility_query completed")
    compatability_percentage = round(int(compatability_query.message.content), 2)
    app.logger.debug("compatability_score is:" + str(compatability_percentage))
    app.logger.debug("resume skills are:" + resume_skills)
    return {
        "compatibility_score": compatability_percentage,
        "compatibility_rating": get_compatibility_message(compatability_percentage),
        "skills": resume_skills,
        "experience": "Ignored for now",
    }
def get_compatibility_message(compatibility):
    """
    Gets the compatibility message based on the compatibility score.
    """
    if compatibility > 80:
        return "high"
    if compatibility > 60:
        return "moderate"
    return "poor"

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
