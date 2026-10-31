import os
from flask import send_from_directory
from api.ocr import app

@app.route('/')
def serve_index():
    # ดึงหน้า index.html จากโฟลเดอร์หลักมาแสดงผล
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, 'index.html')
