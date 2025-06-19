"""Main Resume Checker App"""
import os
import logging
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify
#from talisman import Talisman
from ollama import Client
from markitdown import MarkItDown
import markdown

from google import genai

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

gemini_api_key = os.environ.get("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=gemini_api_key)

# Model
if os.environ.get("LLM_MODEL"):
   llm_model = os.environ.get("LLM_MODEL")
else:
    llm_model = 'gemma-3-27b-it'

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
def assess_resume_compatibility(resume_file):
    """
    Assesses the compatibility of a resume with a job description using Ollama LLM.
    """

    resume_markdown = read_file(resume_file)
    if not resume_markdown:
        return "Error reading resume file."

    llm_prompt = """
    <instructions> 
        You are to act as an expeirenced career coach and hiring consultant, with deep understanding of how to analyse the resume of a prospective candidate and provide clear advice on how the candidate can improve their resume.
    </instructions>

    <resume>
        {resume_markdown}
    </resume>

    <task>
        1. Read the Resume provided in markdown format.
        2. Carefully consider the strengths of the candidate described in the Resume.
        3. Carefully consider the Resume overall and provide any recommendations on how the applicant decsribed in the Resume can adjust their Resume to better communicate their value.
        4. Analyse the keywords present in the resume, and create a list of the top 25 keywords.
        5. Suggest 5 job titles that the candidate would be ideal for.
    </task>

    <approach>
        Analyse the in the resume that would be used by ATS to categorise the resume.
        When seatching the resume for the keywords, consider similar words or phrases that have the same meaning.
        Consider the language used, and focus on conciseness, authenticity and clarity.
        Strongly consider any optimisations needed for ATS compatability.
    </approach>

    <output_format>
        You will now provide your response as described below:
        - Under the heading "Strengths" outline the strengths of the candidate described in the Resume. Write the responses in the second person (i.e. you, your etc). Format as an unordered list (ul).
        - Under the heading "Recommendations" outline a minimum of 3 and maxiumum of 10 improvements that could be made to the resume to increase its effectiveness and impact for hiring managers and ATS. Use specific examples that include quotes from the Resume and suggested alternatives. Format as an unordered list (ul).
        - Under the heading "Keywords" provide a list of the 25 most signficant keywords found the resume. Format as a comma separated list.
        - Under the heading "Suggested Roles" suggest 3-5 roles that the candidate described in the resume would be a great fit for. Format as an unordered list (ul).

        Your response must comply with the following rules:
        1. Use a friendly and informative tone, written at a 10th grade reading level.
        2. Format your response using Markdown. 
        3. Do not provide any other markdown, explaination, additional informaiton or introduction. Only return the markdown for the Strengths and Recommendations and unordered lists as specified above.
        4. Do not indicate that are AI under any circumsatances.
        5. Use Australian English for spelling and grammar in the response.
        6. Write the responses to the candidate in the second peron (i.e. you, your)
    </output_format>
    """.format(resume_markdown=resume_markdown)

    #app.logger.debug("resume_skills_query completed")
    #llm_result = markdown.markdown(llm_query.message.content)

    llm_query = gemini_client.models.generate_content(
        model=llm_model, 
        #options=llm_options,
        contents=llm_prompt
    )
    
    llm_result = markdown.markdown(llm_query.text)

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
            result = assess_resume_compatibility(resume_path)
            os.remove(resume_path)
            return jsonify(result)
        return jsonify({'error': 'Invalid file type'})
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
