from flask import send_from_directory
from api.ocr import app
import os

@app.route('/')
def index():
    # ดึงไฟล์ index.html จากโฟลเดอร์หลักมาแสดงผลหน้าเว็บ
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, 'index.html')
