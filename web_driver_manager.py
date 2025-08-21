from update_manager import UpdateManager

import os
import sys
import shutil
import winreg
import subprocess
import re
import webbrowser

# --- Các thư viện giao diện và web ---
import tkinter as tk
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager



# ==============================================================================
# WEB DRIVER MANAGER CLASS
# ==============================================================================
class WebDriverManager:
    """
    Lớp quản lý trình điều khiển web:
    """

    def __init__(self, window, label):
        self.window = window
        self.label = label

    def initialize_web_driver(self):
        """
        Hàm khởi tạo chính, thử tất cả các phương pháp theo thứ tự ưu tiên.
        """
        print("--- Starting WebDriver Initialization Process ---")

        self._update_label('\nInitializing Edge (manual):')
        # 1. Sử dụng file msedgedriver.exe cục bộ
        try:
            print("▶️ [1/4] Trying to find local msedgedriver.exe...")

            found_path = self._find_file( 'msedgedriver.exe')

            # Giá trị mặc định version = 0 để tải phiên bản mới nhất
            driver_ver = '0'
            if found_path:
                # Kiểm tra version
                version_output = subprocess.check_output([found_path, "--version"], universal_newlines=True)

                # Tìm kiếm phiên bản trong chuỗi output
                match = re.search(r'\d+\.\d+\.\d+\.\d+', version_output)

                # Kiểm tra xem có tìm thấy không
                if match:
                    # Nếu tìm thấy, lấy chuỗi phiên bản ra bằng .group(0)
                    driver_ver = match.group(0) 

            update_manager = UpdateManager()
            release_info = update_manager.check_for_updates(driver_ver, 'Hung-ccan1920/msedgedriver')

            if release_info:
                update_manager.perform_update(release_info['release_info'], 'msedgedriver.exe', False)

            # Tìm lại 
            found_path = self._find_file( 'msedgedriver.exe')

            service = EdgeService(executable_path=found_path)
            options = EdgeOptions()
            options.add_argument("--start-maximized")
            driver = webdriver.Edge(service=service, options=options)
            self._update_label(' Success!')
            print("✅ Success! Using local Edge driver.")
            return driver
        except Exception as e:
            print(f"⚠️ Failed with local Edge file: {e}")

        self._update_label(' Failed!')
        self._update_label('\nInitializing Edge (automatic):')

        # 2. Thử Edge tự động
        try:
            print("▶️ [2/4] Trying to initialize Edge automatically...")
            service = EdgeService(EdgeChromiumDriverManager().install())
            options = EdgeOptions()
            options.add_argument("--start-maximized")
            driver = webdriver.Edge(service=service, options=options)
            self._update_label(' Success!')
            print("✅ Success! Using Microsoft Edge.")
            return driver
        except Exception as e:
            print(f"⚠️ Failed with Edge: {e}")

        self._update_label(' Failed!')
        self._update_label('\nInitializing Chrome:')
        # 3. Thử Chrome tự động
        try:
            print("▶️ [3/4] Trying to initialize Chrome automatically...")
            service = ChromeService(ChromeDriverManager().install())
            options = ChromeOptions()
            options.add_argument("--start-maximized")
            driver = webdriver.Chrome(service=service, options=options)
            self._update_label(' Success!')
            print("✅ Success! Using Google Chrome.")
            return driver
        except Exception as e:
            print(f"⚠️ Failed with Chrome: {e}")

        self._update_label(' Failed!')
        self._update_label('\nInitializing Firefox:')

        # 4. Thử Firefox tự động (với logic tìm kiếm tối ưu)
        try:
            print("▶️ [4/4] Trying to initialize Firefox...")
            options = FirefoxOptions()
            options.add_argument("--start-maximized")
            service = None
            
            # 4.1 Thử cách tự động đơn giản nhất
            print("   -> Trying to find Firefox automatically (standard method)...")
            try:
                service = FirefoxService(GeckoDriverManager().install())       
                driver = webdriver.Firefox(service=service, options=options)
                return driver
            except Exception:
                # 4.2 Nếu lỗi, mới dùng đến hàm tìm kiếm nâng cao
                print("   -> Standard search failed. Trying advanced search...")
                firefox_path = self.find_firefox_executable()
                if not firefox_path:
                    raise ValueError("Could not automatically find Firefox installation path.")
                
                print(f"   -> Found Firefox at: {firefox_path}")
                options.binary_location = firefox_path
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
                self._update_label(' Success!')
                print("✅ Success! Using Firefox.")
                return driver
        except Exception as e:
            print(f"⚠️ Failed with Firefox: {e}")

        # Tất cả đều thất bại, hiển thị thông báo lỗi
        self._update_label(' Failed!')
        print("❌ All methods failed. Displaying message to the user.")
        self._show_webdriver_error_dialog()
        return None

    def _show_webdriver_error_dialog(self):
        """
        Phiên bản đơn giản hóa: Hiển thị hộp thoại Dark Mode, văn bản tự động
        xuống dòng, có hyperlink và nút bấm để MỞ TRANG WEB.
        """
        dialog = tk.Toplevel()
        dialog.title("Lỗi")
        dialog.configure(bg="#2e2e2e")
        dialog.resizable(False, False)

        # --- Thiết lập Dark Mode Style ---
        style = ttk.Style(dialog)
        style.theme_use('clam')
        style.configure(".", background="#2e2e2e", foreground="white", borderwidth=0)
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TButton", background="#444444", foreground="white", font=("Arial", 10, "bold"), padding=5)
        style.map("TButton",
                background=[("active", "#555555"), ("pressed", "#333333")])

        # --- URL để mở ---
        webdriver_url = "https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"

        # --- Widget Text cho thông báo ---
        text_widget = tk.Text(dialog, height=2, wrap='word',
                            background="#2e2e2e", foreground="white",
                            relief="flat", borderwidth=0, highlightthickness=0,
                            font=("Arial", 10))
        text_widget.pack(padx=20, pady=(20, 10))

        # Chèn các phần của văn bản
        text_widget.insert("1.0", "Lỗi Web driver, vui lòng truy cập ")
        link_start_index = text_widget.index(tk.END + "-1c")
        text_widget.insert(tk.END, "Microsoft Edge WebDriver")
        link_end_index = text_widget.index(tk.END + "-1c")
        text_widget.insert(tk.END, " để tải phiên bản mới nhất và giải nén vào thư mục chứa phần mềm.")

        # Tạo tag cho hyperlink
        text_widget.tag_configure("hyperlink", foreground="#66b3ff", underline=True)
        text_widget.tag_add("hyperlink", link_start_index, link_end_index)

        # --- THAY ĐỔI CHÍNH: HÀM CHỈ MỞ WEB ---
        def open_website(event=None):
            webbrowser.open_new_tab(webdriver_url)

        # Gán sự kiện cho hyperlink
        text_widget.tag_bind("hyperlink", "<Enter>", lambda e: text_widget.config(cursor="hand2"))
        text_widget.tag_bind("hyperlink", "<Leave>", lambda e: text_widget.config(cursor=""))
        text_widget.tag_bind("hyperlink", "<Button-1>", open_website)

        # Vô hiệu hóa việc chỉnh sửa trên widget Text
        text_widget.config(state="disabled")

        # --- Khung chứa các nút bấm ---
        button_frame = ttk.Frame(dialog, style="TFrame")
        button_frame.pack(padx=20, pady=(10, 20), fill="x")

        # Tạo nút OK và nút Mở Web
        ok_button = ttk.Button(button_frame, text="OK", command=dialog.destroy)
        open_button = ttk.Button(button_frame, text="Open Web", command=open_website) # Đổi tên và chức năng

        ok_button.pack(side="right", padx=(10, 0))
        open_button.pack(side="right") # Đặt nút Mở Web vào

        # --- Căn giữa và hiển thị cửa sổ ---
        dialog.update_idletasks()

        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x_pos = (screen_width // 2) - (dialog.winfo_width() // 2)
        y_pos = (screen_height // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"{dialog.winfo_width()}x{dialog.winfo_height()}+{x_pos}+{y_pos}")

        dialog.transient()
        dialog.grab_set()
        dialog.focus_set()
        dialog.wait_window()

    def _find_firefox_executable(self):
        """
        Tự động tìm đường dẫn đến file firefox.exe bằng cách kiểm tra các vị trí
        phổ biến, AppData của người dùng và đọc từ Windows Registry.
        """
        # 1. Dùng shutil.which (đơn giản, nhanh nhất)
        path = shutil.which('firefox')
        if path:
            return path

        # 2. Tìm trong thư mục AppData\Local của người dùng hiện tại
        try:
            local_app_data = os.environ.get('LOCALAPPDATA')
            if local_app_data:
                firefox_appdata_path = os.path.join(local_app_data, 'Mozilla Firefox', 'firefox.exe')
                if os.path.exists(firefox_appdata_path):
                    return firefox_appdata_path
        except Exception:
            pass # Bỏ qua nếu có lỗi và thử cách tiếp theo

        # 3. Tìm trong Windows Registry (đáng tin cậy cho các bản cài đặt chuẩn)
        try:
            key_path = r"SOFTWARE\Mozilla\Mozilla Firefox"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                sub_key_name = winreg.EnumKey(key, 0)
                with winreg.OpenKey(key, sub_key_name) as sub_key:
                    return winreg.QueryValueEx(sub_key, 'PathToExe')[0]
        except FileNotFoundError:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    sub_key_name = winreg.EnumKey(key, 0)
                    with winreg.OpenKey(key, sub_key_name) as sub_key:
                        return winreg.QueryValueEx(sub_key, 'PathToExe')[0]
            except FileNotFoundError:
                return None
        except Exception:
            return None
        
        return None

    def _update_label(self, new_text, append=True):
        """Cập nhật nội dung của một đối tượng Label.

        Args:
            new_text: Nội dung mới để hiển thị.
            append (bool): Nếu True, nội dung mới sẽ được nối vào nội dung cũ.
                            Nếu False, nội dung cũ sẽ bị xóa và thay thế bằng nội dung mới.
                            Mặc định là True.
        """
        if self.label and isinstance(self.label, tk.Label):
            if append:
                # Nối nội dung mới vào nội dung hiện tại
                current_text = self.label.cget("text")
                updated_text = current_text + new_text
                self.label.config(text=updated_text)
            else:
                # Thay thế hoàn toàn nội dung cũ
                self.label.config(text=new_text)

            self.window.update_idletasks()

    def _find_file(self, file_name):
        """
        Tìm kiếm một file trong thư mục gốc của ứng dụng và các thư mục con.
        Hàm này giờ độc lập và không cần config.
        """
        
        if getattr(sys, 'frozen', False):
            app_dir =  os.path.dirname(sys.executable)
        else:
            app_dir =  os.path.dirname(os.path.abspath(sys.argv[0]))

        for root, dirs, files in os.walk(app_dir):
            if file_name in files:
                return os.path.join(root, file_name)
        return None