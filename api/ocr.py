import os
import time
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

app = Flask(__name__)
CORS(app)

# ดึง API Key จาก Environment Variable ของ Vercel
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"

def generate_with_retry(model, contents, max_retries=3, initial_delay=3):
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return model.generate_content(contents)
        except (ResourceExhausted, Exception) as e:
            error_str = str(e)
            if "429" in error_str or "ResourceExhausted" in error_str or isinstance(e, ResourceExhausted):
                if attempt == max_retries - 1:
                    raise e
                
                print(f"Rate limit hit (429). Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                delay *= 2
            else:
                raise e

# ดึง index.html จากโฟลเดอร์หลัก (ถอยหลังออกจากโฟลเดอร์ api มา 1 ชั้น)
@app.route('/')
def index():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return send_from_directory(root_dir, 'index.html')

@app.route('/api/ocr', methods=['POST'])
def ocr_handler():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({"error": "No image provided"}), 400

        base64_image = data['image']
        mime_type = data.get('mimeType', 'image/png')

        image_part = {
            "mime_type": mime_type,
            "data": base64_image
        }

        system_prompt = """อ่านข้อมูลจากภาพหน้าจอระบบตรวจสอบรายการผ่านทาง แล้วส่งกลับเป็น JSON ตามฟิลด์ต่อไปนี้:
- platePrefix: หมวดอักษร (เช่น "3ฒล")
- plateNumber: เลขทะเบียน (เช่น "2850")
- province: จังหวัด (เช่น "กรุงเทพมหานคร")
- plaza: ด่าน (เช่น "ทับช้าง 1", "ทับช้าง 2", "ธัญบุรี 1", "ธัญบุรี 2")
- refTripId: Ref Trip Id (เช่น "543212026102900075951074921616A")
- date: วันที่ผ่านทาง (เช่น "29/10/2026")
- timeHm: ชั่วโมง-นาทีผ่านทาง (เช่น "00:07")
- seconds: วินาทีเริ่มต้น (เช่น "59")
- highway: สายทาง
- lane: ช่องทาง"""

        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=system_prompt,
            generation_config={
                "response_mime_type": "application/json"
            }
        )

        response = generate_with_retry(model, [image_part])
        
        result_json = json.loads(response.text)
        return jsonify(result_json)

    except ResourceExhausted:
        return jsonify({"error": "ระบบใช้งานหนาแน่นเกินโควตาชั่วคราว กรุณารอสักครู่แล้วลองกดส่งใหม่อีกครั้ง"}), 429
    except Exception as e:
        print(f"Error in OCR backend: {str(e)}")
        return jsonify({"error": str(e)}), 500

# จำเป็นสำหรับ Vercel Python Serverless
app = app
