from flask import Flask
from threading import Thread
import os
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>🚀 V5 QUANTUM BOT ĐANG HOẠT ĐỘNG!</h1><p>Hệ thống giữ nhịp (Keep-Alive) từ Cron-job.org đang kết nối tốt.</p>"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def start_bot():
    print("Khởi động Bot V5 trên luồng nền...")
    # Tự động cài thư viện nếu thiếu trên cloud, nhưng render đã có requirements.txt
    os.system("python autotyhub_v5.py")

if __name__ == '__main__':
    # 1. Chạy Bot ngầm trên một luồng khác
    t_bot = Thread(target=start_bot)
    t_bot.daemon = True # Cho phép kill luồng khi server tắt
    t_bot.start()
    
    # 2. Chạy Web Server trên luồng chính để Render nhận diện
    run_flask()
