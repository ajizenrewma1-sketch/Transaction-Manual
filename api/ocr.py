import json
import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/api/ocr', methods=['POST'])
def ocr_handler():
  try:
    # 1. รับข้อมูล JSON ที่ส่งมาจากหน้าเว็บ (base64)
    req_data = request.get_json() or {}
    base64_image = req_data.get('image')
    mime_type = req_data.get('mimeType', 'image/jpeg')

    if not base64_image:
      return jsonify({'error': 'No file uploaded'}), 400

    api_key = os.environ.get('GEMINI_API_KEY', '')

    # 2. ตั้งค่า Endpoint ของโมเดล
    url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
    headers = {'Content-Type': 'application/json'}

    payload = {
        'contents': [{
            'parts': [
                {
                    'text': (
                        'คุณคือผู้เชี่ยวชาญการอ่านสลิปใบเสร็จ M-Flow'
                        ' ให้สกัดข้อมูลออกมาเป็น JSON เท่านั้น โดยมีฟิลด์ดังนี้:'
                        ' platePrefix (หมวดอักษร), plateNumber (เลขทะเบียน),'
                        ' province (จังหวัด), plaza (ชื่อด่าน), refTripId'
                        ' (รหัส Ref), date (DD/MM/YYYY ค.ศ.), timeHm (HH:MM),'
                        ' seconds (วินาที), highway (สายทาง), lane (ช่องทาง).'
                    )
                },
                {
                    'inline_data': {
                        'mime_type': mime_type,
                        'data': base64_image,
                    }
                },
            ]
        }],
        'generationConfig': {'response_mime_type': 'application/json'},
    }

    # 3. จัดการ Token แบบ AQ... หรือ API Key แบบปกติ
    if api_key.startswith('AQ.'):
      headers['Authorization'] = f'Bearer {api_key}'
      response = requests.post(url, headers=headers, json=payload)
    elif api_key:
      response = requests.post(
          f'{url}?key={api_key}', headers=headers, json=payload
      )
    else:
      response = requests.post(url, headers=headers, json=payload)

    if not response.ok:
      return jsonify({'error': f'Gemini API Error: {response.text}'}), response.status_code

    res_data = response.json()

    # 4. แกะข้อมูล JSON ที่ Gemini ตอบกลับมา
    try:
      candidate = res_data['candidates'][0]['content']['parts'][0]['text']
      if '```json' in candidate:
        candidate = candidate.split('```json')[1].split('```')[0].strip()
      elif '```' in candidate:
        candidate = candidate.split('```')[1].split('```')[0].strip()

      parsed_json = json.loads(candidate)
      return jsonify(parsed_json)
    except Exception:
      return jsonify(res_data)

  except Exception as e:
    return jsonify({'error': str(e)}), 500
