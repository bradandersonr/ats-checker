# ATS Resume Checker
[![Publish Docker image](https://github.com/bradandersonr/ats-checker/actions/workflows/docker-image.yml/badge.svg)](https://github.com/bradandersonr/ats-checker/actions/workflows/docker-image.yml) [![Pylint](https://github.com/bradandersonr/ats-checker/actions/workflows/pylint.yml/badge.svg)](https://github.com/bradandersonr/ats-checker/actions/workflows/pylint.yml)

A web application that helps job seekers evaluate their resume's compatibility with job description.

## Features

- Upload and analyze resumes in PDF or DOCX format
- Compare resume content against job descriptions

## Prerequisites

- Python `3.12`

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Environment
The following environment variables should be set:
```bash
FLASK_DEBUG=False
FLASK_APP=app/main.py
```

You will also need to provide a API Key to use Gemini services. This can be done in two ways:
1. Directly using an Environment variable:
```bash
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
```

2. Using a 'Secret' in Docker, that would be read from a file, but setting the following variable:
```bash
GEMINI_API_KEY_FILE=</path/to/GEMINI_API_KEY>
```

## Usage

1. Start the application:

```bash
flask run --debug
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Upload your resume (PDF or DOCX format) and paste the job description

4. Click "Analyze" to get your compatibility score and assessment



#