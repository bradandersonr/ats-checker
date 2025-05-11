"""Main Resume Checker App"""
import os
import logging
import nltk
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify
from simple_ats.ats import ATS
from talisman import Talisman

nltk.download('punkt_tab')

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

Talisman(app, content_security_policy={
    'default-src': '\'self\'',
    'script-src': '\'self\' cdn.jsdelivr.net',
    'style-src': '\'none\'',
    'object-src': '\'none\'',
    'frame-ancestors': '\'none\'',
    'require-trusted-types-for': '\'script\''
})

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
        if file_path.lower().endswith(".docx"):
            from docx import Document
            doc = Document(file_path)
            return " ".join(p.text for p in doc.paragraphs)
        if file_path.lower().endswith(".pdf"):
            import PyPDF2
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                return "".join(page.extract_text() or "" for page in reader.pages)
        raise ValueError("Unsupported file format. Please use .docx or .pdf.")
    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"Error reading file: {e}")
        return ""

def assess_resume_compatibility(job_description, resume_file):
    """
    Assesses the compatibility of a resume with a job description using simple-ats.
    """
    if not job_description or not resume_file:
        return "Error: Job description or resume file is empty."

    resume_text = read_file(resume_file)
    if not resume_text:
        return "Error reading resume file."

    ats = ATS()

    ats.load_resume(resume_text)
    ats.load_job_description(job_description)

    # Extract and clean experience
    experience = ats.extract_experience()
    ats.clean_experience(experience)

    # Extract and clean skills
    skills = " ".join(ats.extract_skills())
    ats.clean_skills(skills)

    compatibility_score = ats.compute_similarity()
    percentage_compatibility = round(compatibility_score.item() * 100, 2)

    return {
        "compatibility_score": percentage_compatibility,
        "compatibility_rating": get_compatibility_message(percentage_compatibility),
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
    app.run(debug=True)
