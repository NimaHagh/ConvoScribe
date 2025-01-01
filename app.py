from flask import Flask, render_template, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF for PDF processing
from openai import OpenAI
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_pdf(file_path):
    """
    Extract text from a PDF file.
    """
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def process_txt(file_path):
    """
    Read text from a TXT file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_summary(content, template):
    """
    Use OpenAI API to generate a structured summary.
    """
    prompt = f"Here are the meeting notes:\n\n{content}\n\nUsing the '{template}' template, provide a structured summary with key points, decisions, and action items."
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant that generates structured meeting summaries."},
            {"role": "user", "content": prompt}
        ]
    )
    summary = response.choices[0].message.content.strip()
    return summary

@app.route('/')
def landing_page():
    return render_template('landing.html')

@app.route('/submit', methods=['GET'])
def submission_form():
    return render_template('submit.html')

@app.route('/process', methods=['POST'])
def process_submission():
    try:
        # Get form data
        title = request.form.get('title')
        template = request.form.get('template')

        # Handle file upload
        if 'audio_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['audio_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file type'}), 400

        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Process file content
        if filename.endswith('.pdf'):
            content = process_pdf(file_path)
        elif filename.endswith('.txt'):
            content = process_txt(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        # Generate summary using OpenAI
        summary = generate_summary(content, template)

        # Create a temporary file for download
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_file:
            temp_file.write(summary)
            temp_file_path = temp_file.name

        # Return the downloadable file
        return send_file(temp_file_path, as_attachment=True, download_name=f"{title}_summary.txt")

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
