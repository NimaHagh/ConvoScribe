from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Configure upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
        email = request.form.get('email')
        template = request.form.get('template')
        use_trello = request.form.get('use_trello') == 'true'

        # Handle file upload
        if 'audio_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['audio_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Process file and return success
        return jsonify({
            'message': 'Submission received successfully',
            'title': title,
            'email': email
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)