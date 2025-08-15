import utils
from config_manager import ConfigManager
from update_manager import UpdateManager

import gui
import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
import queue

MAIN_CURRENT_VERSION = "3.0" 
MAIN_GITHUB_REPO = "Hung-ccan1920/Hoa-don" 

# Chỉ import và sử dụng pyi_splash khi chạy dưới dạng .exe
if getattr(sys, 'frozen', False):
    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass

os.environ["PYTHONOPTIMIZE"] = "1"

def main():
    # 1. Tạo đối tượng quản lý cấu hình duy nhất cho toàn bộ ứng dụng
    config = ConfigManager(app_name="ChuyenTriHoaDon")
    update_manager = UpdateManager()

    # 2. Tự động kiểm tra các thông tin bắt buộc và hiện cửa sổ yêu cầu nhập nếu thiếu
    config.check_and_prompt_for_missing()

    # Truyền đối tượng `config` vào hàm tạo giao diện
    window = gui.create_gui(MAIN_CURRENT_VERSION, config)
    
    # Logic kiểm tra cập nhật
    update_queue = queue.Queue()

    update_thread = threading.Thread(
        target=lambda q, cv, repo: q.put(update_manager.check_for_updates(cv, repo)),
        args=(update_queue, MAIN_CURRENT_VERSION, MAIN_GITHUB_REPO),
        daemon=True
    )
    update_thread.start()

    def handle_update_result():
        try:
            update_result = update_queue.get_nowait()
            if update_result:
                version_tag = update_result["version_tag"]
                release_info = update_result["release_info"]
                
                if messagebox.askyesno("New Version Available",
                                     f"A new version {version_tag} is available!\nDo you want to update now?"):
                    update_manager.perform_update(release_info, None, True)
        except queue.Empty:
            window.after(1000, handle_update_result)

    window.after(2000, handle_update_result)
    window.mainloop()


if __name__ == "__main__":
    main()