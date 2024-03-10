import os

from flask import Flask
from flask import Flask, send_file
from flask_cors import CORS
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import json

import base

# get env debug
DEBUG = os.environ.get('DEBUG', False)

# init server
app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['debug'] = False
CORS(app)

# Configuration
UPLOAD_FOLDER = 'server/docs'  # Define the directory to save uploaded files
ALLOWED_EXTENSIONS = {'pdf'}  # Allowed file extensions

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    # Check if file has one of the allowed extensions
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# init resume expert
resume_expert_client = base.ResumeExpert()

@app.route("/api/generate", methods=['GET', 'POST'])
def run_resume_optimization():

    # read formdata from request
    resume_path = request.form.get('resume_path')
    job_ad_text = request.form.get('job_ad_text')
    
    #
    try:
        resume_url, resume_docx_url, cover_url, cover_docx_url , cover_letter_text = resume_expert_client.generate(resume_path=resume_path, job_ad_text=job_ad_text)
        

        #
        response = {
            "resume_url": resume_url, 
            "cover_url": cover_url, 
            "resume_docx_url": resume_docx_url,
            "cover_docx_url": cover_docx_url,
            "cover_letter_text": cover_letter_text
        }
    except Exception as e:
        response = {
            "error": str(e)
        }
        return json.dumps(response, ensure_ascii=False), 500


    return json.dumps(response, ensure_ascii=False), 200 


@app.route("/api/upload", methods=['GET', 'POST'])
def writefile():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        return jsonify({'message': f'File {filename} uploaded successfully', 'path': save_path}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400


@app.route('/api/download', methods=['GET'])
def download_file():
    filename = request.args.get('filename')
    path = os.path.join("./docs", filename)
    print(path)

    return send_file(path, as_attachment=True)

   

@app.route('/api/downloads', methods=['GET'])
def ping():
    print("asd")
    return jsonify({'error': 'ping'}), 200

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'This is a test.'}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)	# run server