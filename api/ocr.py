import base64
import json
import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/api/ocr', methods=['POST'])
def ocr_handler():
  try:
    api_key = os.environ.get('GEMINI_API_KEY')
    # ดึงไฟล์ภาพจาก Request
    file = request.files.get('file')
    if not file:
      return jsonify({'error': 'No file uploaded'}), 400

    image_bytes = file.read()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    # กำหนด URL และ Payload สำหรับ Gemini 1.5 Flash
    url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'

    headers = {'Content-Type': 'application/json'}

    payload = {
        'contents': [{
            'parts': [
                {
                    'text': (
                        'Extract all relevant OCR receipt data into JSON'
                        ' format.'
                    )
                },
                {
                    'inline_data': {
                        'mime_type': file.content_type or 'image/jpeg',
                        'data': base64_image,
                    }
                },
            ]
        }]
    }

    # ตรวจสอบประเภท คีย์
    if api_key.startswith('AQ.'):
      # กรณีเป็น Token แบบ AQ... ส่งผ่าน Authorization Header
      headers['Authorization'] = f'Bearer {api_key}'
      response = requests.post(url, headers=headers, json=payload)
    else:
      # กรณีเป็น API Key แบบ AIza... ส่งผ่าน Query Param
      response = requests.post(
          f'{url}?key={api_key}', headers=headers, json=payload
      )

    res_data = response.json()
    return jsonify(res_data)

  except Exception as e:
    return jsonify({'error': str(e)}), 500
