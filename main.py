import os
import csv
import io
import datetime
from flask import Flask, request, jsonify
from google.cloud import storage
from werkzeug.utils import secure_filename

BUCKET_NAME = "my-first-project-12"

app = Flask(__name__)
storage_client = storage.Client()

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        registration_number = request.form.get('no') 
        
        uploaded_file = request.files.get('file') 
        
        if not registration_number:
            registration_number = "NO_REG_NO"

        unique_folder = f"submission_{timestamp_str}_{registration_number}"
        
        bucket = storage_client.bucket(BUCKET_NAME)

        form_data = {
            'Full Name': request.form.get('fname'),
            'VIT Email': request.form.get('email'),
            'Registration Number': request.form.get('no'),
            'No. of participants': request.form.get('project'),
        }
        
        image_gcs_path = "N/A"
        if uploaded_file and uploaded_file.filename:
            image_gcs_path = f"gs://{BUCKET_NAME}/{unique_folder}/payment_screenshot_{secure_filename(uploaded_file.filename)}"
            
        form_data['Payment File GCS Path'] = image_gcs_path
        
        csv_buffer = io.StringIO()
        fieldnames = list(form_data.keys())
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerow(form_data)
        
        metadata_blob = bucket.blob(f"{unique_folder}/metadata.csv")
        metadata_blob.upload_from_string(csv_buffer.getvalue(), content_type='text/csv')

        if uploaded_file and uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)
            blob_path = f"{unique_folder}/payment_screenshot_{filename}"
            blob = bucket.blob(blob_path)
            
            file_contents = uploaded_file.read()
            
            content_type = uploaded_file.content_type if uploaded_file.content_type else 'application/octet-stream'

            blob.upload_from_string(file_contents, content_type=content_type)
            
            print(f"File uploaded successfully to: gs://{BUCKET_NAME}/{blob_path}")

        return jsonify({
            "message": "Success! Registration data and payment proof saved.",
            "gcs_folder": f"gs://{BUCKET_NAME}/{unique_folder}"
        }), 200

    except Exception as e:
        print(f"An unhandled error occurred during submission: {e}")
        return jsonify({"error": f"Submission failed due to a server error. Please check the logs."}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))