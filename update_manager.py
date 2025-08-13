import os
import subprocess
import sys
from tkinter import messagebox
import requests
from packaging.version import parse as parse_version



# ==============================================================================
# UPDATE MANAGER CLASS
# ==============================================================================
class UpdateManager:
    """
    Lớp quản lý cập nhật phần mềm:
    """

    def __init__(self):
        pass

    def check_for_updates(self, current_version, github_repo):
        """
        Kiểm tra cập nhật trên GitHub.

        Trả về:
            - Một dictionary chứa thông tin cập nhật nếu có bản mới:
                "version_tag": latest_version_tag
                "release_info": latest_release
            - None nếu không có bản mới hoặc có lỗi.
        """
        try:
            print("Checking for new version in the background...")
            api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
            response = requests.get(api_url, timeout=5)
            response.raise_for_status() # Gây ra một exception nếu status code không tốt (4xx hoặc 5xx)

            latest_release = response.json()
            latest_version_tag = latest_release["tag_name"]
            latest_version = latest_version_tag.lstrip('v') # Xóa tiền tố 'v' nếu có

            if parse_version(latest_version) > parse_version(current_version):
                print(f"Update found: {latest_version_tag}")
                # Trả về thông tin cần thiết để file main xử lý
                return {
                    "version_tag": latest_version_tag,
                    "release_info": latest_release
                }
            else:
                print("You are using the latest version.")
                return None
                
        except requests.exceptions.RequestException as e:
            # Xử lý các lỗi liên quan đến request (ví dụ: lỗi mạng, timeout)
            print(f"Error checking for updates (network issue): {e}")
            return None
        except Exception as e:
            # Xử lý các lỗi tiềm ẩn khác (ví dụ: phân tích JSON, lỗi key)
            print(f"An unexpected error occurred while checking for updates: {e}")
            return None

    def perform_update(self, release_info, app_name=None, is_exit_app=True):
        """
        Hàm này chứa logic gọi updater.exe để thực hiện cập nhật.
        Nó sẽ được gọi bởi main.py sau khi người dùng đồng ý.
        Args:
            release_info: thông tin bản release
            app_name: tên file khác cần update, nếu None: là chính app đang chạy
            is_exit_app: True: tắt app, đợi update xong thì khởi động lại app
                        False: không tắt app, nhưng phải đợi update xong mới tiếp tục app
        """
        try:
            if not release_info.get("assets"):
                messagebox.showerror("Error", "Update file not found in the new release!")
                return

            asset = release_info["assets"][0]
            download_url = asset["browser_download_url"]

            if getattr(sys, 'frozen', False):
                app_path = os.path.basename(sys.executable)
            else:
                app_path = os.path.basename(os.path.abspath(sys.argv[0]))

            app_dir = os.path.dirname(app_path)

            # Tìm updater.exe trong thư mục gốc và thư mục con
            updater_path = self._find_file("updater.exe")

            if app_name:
                target_path = self._find_file(app_name)
                if not target_path:
                    target_path = os.path.join(app_dir, app_name)
            else: # chưa viết hàm kiểm tra file gọi từ file py không để xử lý không bị lỗi thay thế file py
                target_path = app_path

            # Nếu tìm thấy thì gọi updater, ngược lại báo lỗi
            if updater_path:
                print(f"✅ Updater found: {updater_path}")
                print("🚀 Calling updater to perform the update...")
                if is_exit_app:
                    subprocess.Popen([updater_path, target_path, download_url])
                    sys.exit()
                else:
                    # subprocess.run sẽ đợi tiến trình con hoàn thành
                    subprocess.run([updater_path, target_path, download_url], check=True)
            else:
                print("❌ updater.exe not found!")
                messagebox.showerror("Update Error", "'updater.exe' not found to perform the update.")
                
        except Exception as e:
            messagebox.showerror("Update Error", f"An error occurred during the update process: {e}")
    
    def _find_file(self, file_name):
        """
        Tìm kiếm một file trong thư mục gốc của ứng dụng và các thư mục con.
        Hàm này giờ độc lập và không cần config.
        """
        
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        for root, dirs, files in os.walk(app_dir):
            if file_name in files:
                return os.path.join(root, file_name)
        return None