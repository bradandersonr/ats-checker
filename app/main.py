import os
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify
from simple_ats.ats import ATS
import tempfile
import logging
import nltk
nltk.download('punkt_tab')

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

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
        elif file_path.lower().endswith(".pdf"):
            import PyPDF2
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                return "".join(page.extract_text() or "" for page in reader.pages)
        else:
            raise ValueError("Unsupported file format. Please use .docx or .pdf.")
    except Exception as e:
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

    # Use simple-ats to compare the files
    with tempfile.NamedTemporaryFile(mode='w+t', delete=True) as job_temp, \
            tempfile.NamedTemporaryFile(mode='w+t', delete=True) as resume_temp:
        job_temp.write(job_description)
        resume_temp.write(resume_text)
        job_temp.seek(0)
        resume_temp.seek(0)

        #
        #resume_content = job_temp.name
        #jd_content = resume_temp.name

        resume_content = resume_text
        jd_content = job_description

        ats = ATS()

        ats.load_resume(resume_content)
        ats.load_job_description(jd_content)

        # Extract and clean experience
        experience = ats.extract_experience()
        ats.clean_experience(experience)

        # Extract and clean skills
        skills = " ".join(ats.extract_skills())
        ats.clean_skills(skills)

        similarity_score = ats.compute_similarity()        
        percentage_similarity = round(similarity_score.item() * 100, 2)

    return {
        "similarity_score": percentage_similarity,
        "compatibility_message": get_compatibility_message(percentage_similarity),
    }


def get_compatibility_message(similarity):
    """
    Gets the compatibility message based on the similarity score.
    """
    if similarity > 80:
        return "The resume is highly compatible with the job description."
    elif similarity > 60:
        return "The resume is moderately compatible with the job description."
    else:
        return "The resume is not very compatible with the job description."



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
        else:
            return jsonify({'error': 'Invalid file type'})
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
