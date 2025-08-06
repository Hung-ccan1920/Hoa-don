import gui
import utils
import sys
import tab2
import password_manager


import os
import time
import requests
import subprocess
import tkinter as tk
from tkinter import messagebox
from packaging.version import parse as parse_version

import threading # Thư viện để xử lý đa luồng
import queue

MAIN_CURRENT_VERSION = "2.8" 
MAIN_GITHUB_REPO = "Hung-ccan1920/Hoa-don" 

# Chỉ import và sử dụng pyi_splash khi chạy dưới dạng .exe
if getattr(sys, 'frozen', False):
    try:
        import pyi_splash
        # Đóng splash sau 2 giây (có thể điều chỉnh)
        # time.sleep(2)
        pyi_splash.close()
    except ImportError:
        pass  # Bỏ qua nếu pyi_splash không khả dụng (chạy trực tiếp)

os.environ["PYTHONOPTIMIZE"] = "1"

def main():
    # Bước 1: Hoàn thành các tác vụ chặn ban đầu
    # Kiểm tra và yêu cầu nhập API key và Excel nếu chưa có
    utils.manage_config_file(['API key', 'Excel'])
    # Mã hóa mật khẩu
    password_manager.password_manager()

    # Bước 2: Tạo màn hình chính
    window = gui.create_gui(MAIN_CURRENT_VERSION)
    
    # 3. Tạo "hộp thư" để giao tiếp
    update_queue = queue.Queue()

    # 4. Khởi chạy luồng nền để kiểm tra cập nhật
    update_thread = threading.Thread(
        target=lambda q, cv, repo: q.put(utils.check_for_updates(cv, repo)),
        args=(update_queue, MAIN_CURRENT_VERSION, MAIN_GITHUB_REPO),
        daemon=True
    )
    update_thread.start()

    # 5. Định nghĩa hàm xử lý kết quả từ luồng nền
    def handle_update_result():
        try:
            update_result = update_queue.get_nowait()
            if update_result:
                # Nếu có bản cập nhật, hiển thị hộp thoại
                version_tag = update_result["version_tag"]
                release_info = update_result["release_info"]
                
                if messagebox.askyesno("Có phiên bản mới",
                                     f"Phiên bản mới {version_tag} đã sẵn sàng!\nBạn có muốn cập nhật không?"):
                    utils.perform_update(release_info,None,True)
            # Dù có phiên bản mới hay không, không cần lên lịch chạy lại nữa.
        except queue.Empty:
            # Nếu luồng nền chưa chạy xong, kiểm tra lại sau 1 giây
            window.after(1000, handle_update_result)

    # 6. Lên lịch để bắt đầu kiểm tra hộp thư sau 2 giây (để giao diện ổn định)
    window.after(2000, handle_update_result)

    # 7. Chạy vòng lặp chính của giao diện
    window.mainloop()


if __name__ == "__main__":
    main()