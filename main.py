import utils
import tab1
import tab2
from config_manager import ConfigManager
from update_manager import UpdateManager

import gui
import sys
import os
from tkinter import messagebox
import threading
import queue

MAIN_CURRENT_VERSION = "3.5" 
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
    # Khởi tạo đối tượng quản lý cấu hình
    config = ConfigManager(app_name="ChuyenTriHoaDon")

    # Tự động kiểm tra các thông tin bắt buộc và hiện cửa sổ yêu cầu nhập nếu thiếu
    config.check_and_prompt_for_missing()

    # Check if a command-line argument was provided
    if len(sys.argv) > 1:
        if "tab1" in sys.argv[1]:
            # The first argument (sys.argv[1]) is the full data string from VBA
            input_string = sys.argv[2]
            # Define the keys in the exact order they appear in the data string from VBA
            # A, I, L, M, (K-J), K
            keys = ["Goi", "MST", "KHHDon", "SHDon", "TgTThue", "TgTTTBSo"]

            # Process the string to get the defaultdict
            processed_invoices = utils.process_data_from_vba(keys,input_string)

            tab1.lookup_invoices_interactive(None,None,config,processed_invoices)
        elif "tab2" in sys.argv[1]:
            tab2.web_open(None, None, config)

    else:
        update_manager = UpdateManager()

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