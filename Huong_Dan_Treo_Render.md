# Hướng Dẫn Treo AUTO Render 24/7 (Miễn Phí) Bằng Cron-Job.org

Render.com cho phép bạn treo code Python 24/7 miễn phí dưới dạng **Web Service**. Tuy nhiên, nếu bạn không có ai truy cập vào link web của bạn trong vòng 15 phút, máy chủ sẽ tự động NGỦ (sleep). Để giữ bot luôn sống, chúng ta dùng **Cron-job.org** để chọc (ping) vào web mỗi 5 phút một lần.

Để làm được điều này, Bot của anh (bản chất là một ứng dụng chạy ngầm Terminal) cần được bọc thêm một cái Vỏ Web Server (dùng thư viện Flask) tĩnh để Render hiểu đây là một Web Service.

Dưới đây là các bước chi tiết để anh đưa dự án này lên Render:

---

## BƯỚC 1: Sửa mã nguồn (Thêm Web Server vào Bot)

Anh tạo một file mới tên là `main.py` ngang hàng với file `autotyhub_v5.py` và dán đoạn code này vào:

```python
from flask import Flask
from threading import Thread
import asyncio
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 V5 QUANTUM BOT ĐANG HOẠT ĐỘNG!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def start_bot():
    print("Khởi động Bot nền...")
    os.system("python autotyhub_v5.py")

if __name__ == '__main__':
    # Chạy Bot ngầm trên một luồng khác
    t_bot = Thread(target=start_bot)
    t_bot.start()
    
    # Chạy Web Server trên luồng chính để Render nhận diện
    run_flask()
```

## BƯỚC 2: Chuẩn Bị Tệp Yêu Cầu `requirements.txt`
Render cần biết bạn dùng thư viện gì để nó tải về. Tạo file `requirements.txt` với nội dung:
```text
flask
aiohttp
colorama
requests
```

## BƯỚC 3: Upload Lên GitHub
1. Tạo một Repository Mới trên [GitHub.com](https://github.com/).
2. Tải tất cả các file sau lên GitHub của anh (KHÔNG ĐƯA THƯ MỤC CŨ, CHỈ ĐÚNG CÁC FILE NÀY):
   - `main.py`
   - `autotyhub_v5.py`
   - `data.txt` (Chứa token của anh)
   - `requirements.txt`

## BƯỚC 4: Triển Khai Lên Render.com
1. Đăng nhập [Render.com](https://render.com/).
2. Chọn **New** -> **Web Service**.
3. Chọn _"Build and deploy from a Git repository"_ và kết nối với cái kho GitHub anh vừa tải code lên.
4. Ở màn hình cấu hình, chọn y đúc như sau:
   - **Name**: tyhub-auto-v5 (hoặc tên gì tuỳ anh)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: Miễn Phí (Free).
5. Bấm **Create Web Service**. Chờ tầm 3-5 phút cho máy chủ khởi động chữ *In Progress* chuyển sang *Live*.
6. Lưu lại cái Link mà Render cấp cho anh (Ví dụ: `https://tyhub-auto-v5.onrender.com`). Bấm vào link đó thấy chữ "V5 QUANTUM BOT ĐANG HOẠT ĐỘNG!" là thành công! BOT LÚC NÀY BẮT ĐẦU CHẠY RỒI.

## BƯỚC 5: Móc Cron-job.org Tránh Bot Ngủ Gật
1. Truy cập [Cron-job.org](https://cron-job.org/) và tạo tài khoản.
2. Bấm **CREATE CRONJOB**.
3. Phần **URL**: Dán cái link web mà Render vừa cấp cho anh ban nãy vào đây (Cái link đuôi `.onrender.com`).
4. Phần **Schedule**: Đánh dấu vào cột chọn **Every 5 Minutes**.
5. Bấm **Create**. XONG!

Bây giờ Cứ 5 phút Cron-job sẽ gửi một nhịp tim (ping) vào con Bot Render của anh. Render thấy có người truy cập nó sẽ KHÔNG BAO GIỜ NGỦ. Bot của anh sẽ cày Kim Cương bay 24/24 suốt đời cho đến khi hết dung lượng Render Free của tháng thì thôi!
