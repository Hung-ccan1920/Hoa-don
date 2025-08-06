from collections import defaultdict

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
import webbrowser

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog

from lxml import etree

import os

import google.generativeai as genai

import PIL.Image

import fitz 

from datetime import datetime

import glob

import sys

import shutil
import winreg

import requests
import subprocess
from packaging.version import parse as parse_version

import re


GE_MODEL = "gemini-2.0-flash"
key_count = 0
api_key = None

def check_for_updates(current_version, github_repo):
    """
    Kiểm tra cập nhật trên GitHub.
    Trả về:
        - Một dictionary chứa thông tin cập nhật nếu có bản mới.
        - None nếu không có bản mới hoặc có lỗi.
    """
    try:
        print("Đang kiểm tra phiên bản mới ở chế độ nền...")
        api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()

        latest_release = response.json()
        latest_version_tag = latest_release["tag_name"]
        latest_version = latest_version_tag.lstrip('v')

        if parse_version(latest_version) > parse_version(current_version):
            print(f"Đã tìm thấy bản cập nhật: {latest_version_tag}")
            # Trả về thông tin cần thiết để file main.py xử lý
            return {
                "version_tag": latest_version_tag,
                "release_info": latest_release
            }
        else:
            print("Bạn đang dùng phiên bản mới nhất.")
            return None
    except Exception as e:
        print(f"Lỗi khi kiểm tra cập nhật: {e}")
        return None

def perform_update(release_info, app_name=None, is_exit_app=True):
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
            messagebox.showerror("Lỗi", "Không tìm thấy file cập nhật trong bản phát hành mới!")
            return

        asset = release_info["assets"][0]
        download_url = asset["browser_download_url"]

        app_path = get_app_path()
        app_dir = os.path.dirname(app_path)

        # Tìm updater.exe trong thư mục gốc và thư mục con
        updater_path = find_file(app_dir, "updater.exe")

        if app_name:
            target_path = find_file(app_dir, app_name)
            if not target_path:
                target_path = os.path.join(app_dir, app_name)
        else:# chưa viết hàm kiểm tra file gọi từ file py không để xử lý khôgn bị lỗi thay thế file py
            target_path = app_path

        # Nếu tìm thấy thì gọi updater, ngược lại báo lỗi
        if updater_path:
            print(f"✅ Tìm thấy updater: {updater_path}")
            print("🚀 Đang gọi updater để cập nhật...")
            if is_exit_app:
                subprocess.Popen([updater_path, target_path, download_url])
                sys.exit()
            else:
                subprocess.run([updater_path, target_path, download_url])
        else:
            print("❌ Không tìm thấy updater.exe!")
            messagebox.showerror("Lỗi cập nhật", "Không tìm thấy 'updater.exe' để thực hiện cập nhật.")
    except Exception as e:
        messagebox.showerror("Lỗi Cập Nhật", f"Lỗi trong quá trình cập nhật: {e}")


def manage_config_file(require_list):
    '''
    Hàm kiểm tra và bắt cập nhật thông tin trong file config.
    require_list: list các key yêu cầu.
    '''
    config_path = find_file('config.txt')

    if not (os.path.exists(config_path)) or ':' not in open(config_path, 'r', encoding='utf-8').read() :
        with open(config_path, 'w', encoding='utf-8') as file:
            for require in require_list:
                file.write(f'{require}:\n')

    with open(config_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    missing_data = []
    line_indices = []
    for i, line in enumerate(lines):
        if ':' in line:
            key, value = line.split(':', 1)
            if not value.strip():
                missing_data.append(key.strip())
                line_indices.append(i)

    if not missing_data:
        return

    # Tạo cửa sổ giao diện chính
    window = tk.Tk()
    window.title("Cập nhật file config")
    window.geometry(window_center_position(350, 200)) 
    window.config(bg="#2e2e2e")
    window.resizable(False, False)
    window.attributes('-topmost', True) # Giữ cửa sổ luôn ở trên

    def on_closing():
    # Hiển thị hộp thoại hỏi xác nhận
        window.destroy()
        sys.exit() # Thoát hoàn toàn ứng dụng

    # Gắn hàm on_closing với sự kiện nhấn nút 'X' trên thanh tiêu đề
    window.protocol("WM_DELETE_WINDOW", on_closing)
    style = ttk.Style(window)
    style.theme_use("clam")

    # Style cho Frame nền
    style.configure("TFrame", background="#2e2e2e")

    # Style cho nút lớn (copy từ màn hình chính của bạn)
    style.configure("Dark.TButton",
                    background="#444444",
                    foreground="white",
                    font=("Arial", 10, "bold"),
                    borderwidth=2,
                    padding=10,
                    relief="raised")
    style.map("Dark.TButton",
              background=[("active", "#555555")],
              relief=[("pressed", "sunken")])

    # Style mới cho các nút nhỏ "Hướng dẫn" và "..."
    style.configure("Small.TButton",
                    font=("Arial", 8, "bold"),
                    padding=(2, 2)) # Padding nhỏ hơn
    style.map("Small.TButton",
              background=[("active", "#555555"), ('!disabled', '#444444')],
              foreground=[('!disabled', 'white')],
              relief=[("pressed", "sunken")])


    def update_values():
        all_filled = True
        for i, entry in enumerate(entry_widgets):
            if not entry.get().strip():
                messagebox.showwarning("Cảnh báo", f"Giá trị cho '{missing_data[i]}' không được để trống!")
                all_filled = False
                break 
        
        if all_filled:
            for i, entry in enumerate(entry_widgets):
                new_value = entry.get().strip()
                lines[line_indices[i]] = f"{missing_data[i]}: {new_value}\n"
            
            with open(config_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
            
            messagebox.showinfo("Thành công", "Đã cập nhật file config thành công!")
            window.destroy()

    def open_api_guide():
        video_path = find_file('Get API key.mp4')
        if video_path:
            try:
                webbrowser.open(video_path)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở file video: {e}")
        else:
            messagebox.showwarning("Không tìm thấy", f"Không tìm thấy file 'Get API key.mp4' trong thư mục ứng dụng.")

    def choose_excel_file(entry_widget):
        file_path = filedialog.askopenfilename(
            title="Chọn file Excel",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)

    tk.Label(window, text="Vui lòng nhập các giá trị còn thiếu:", fg="white", bg="#2e2e2e", font=("Arial", 12)).pack(pady=(10, 5))

    entry_widgets = []
    for key in missing_data:
        # Thay thế tk.Frame bằng ttk.Frame để đồng bộ style
        frame = ttk.Frame(window, style="TFrame")
        frame.pack(pady=5, fill="x", padx=15)

        tk.Label(frame, text=f"{key}:", fg="white", bg="#2e2e2e", font=("Arial", 10), width=15, anchor="w").pack(side="left")
        
        choose_button = None
        
        # 1. Nếu là API key, thêm nút "Hướng dẫn" (sử dụng ttk.Button)
        if 'api' in key.lower():
            guide_button = ttk.Button(frame, text="?", style="Small.TButton", width=3, command=open_api_guide)
            guide_button.pack(side="right", padx=(5, 0))

        # 2. Nếu là Excel, thêm nút "..." để chọn file (sử dụng ttk.Button)
        elif 'excel' in key.lower():
            choose_button = ttk.Button(frame, text="...", style="Small.TButton", width=3)
            choose_button.pack(side="right", padx=(5, 0))
        
        # Cải thiện giao diện ô nhập liệu cho phù hợp
        entry = tk.Entry(frame, font=("Arial", 10), bg="#555555", fg="white", insertbackground="white", relief="solid", borderwidth=1)
        entry.pack(side="left", expand=True, fill="x")
        entry_widgets.append(entry)
        
        if choose_button:
             choose_button.config(command=lambda e=entry: choose_excel_file(e))

    # Nút chính sử dụng style "Dark.TButton" (sử dụng ttk.Button)
    ttk.Button(
        window,
        command=update_values,
        text="Save",
        style="Dark.TButton"
    ).pack(pady=20)

    window.mainloop()

def config_file_value(key) -> list:
    """Hàm truy xuất thông tin trong file config theo key."""

    if not key:
        raise ValueError("Key không được rỗng.")

    try:
        with open('config.txt', 'r', encoding='utf-8') as config_file:
            for line in config_file:
                if key.lower() in line.lower():
                    if ":" in line:
                        # Sử dụng list comprehension để rút gọn code
                        return [value.strip() for value in line.split(":", 1)[1].strip().split(',')]
        # Tìm không thấy trả về none
        return None
    except FileNotFoundError:
        messagebox.showerror('Lỗi', f"Không tìm thấy file config: config.txt")
    except Exception as e:
        messagebox.showerror('Lỗi', f"Lỗi khi đọc file config: {e}")

    return []  # Trả về list rỗng nếu không tìm thấy key

def write_config_file (key, value):
    '''Hàm ghi giá trị vào file config theo key'''

    # Đọc tất cả các dòng từ file config vào một danh sách
    with open('config.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Tìm và cập nhật dòng chứa key
    found = False
    for i, line in enumerate(lines):
        # Dùng .strip() và .lower() để linh hoạt hơn
        if line.strip().lower().startswith(f'{key.strip().lower()}:'):
            lines[i] = f'{key}: {value}\n'
            found = True
            break
    
    # Nếu không tìm thấy key, thêm nó vào cuối
    if not found:
         lines.append(f'{key}: {value}\n')

    # Ghi lại toàn bộ nội dung đã cập nhật vào file
    with open('config.txt', 'w', encoding='utf-8') as f:
        f.writelines(lines)

def window_center_position(width, height)->str:
    window = tk.Tk()
    window.withdraw()

    # Lấy kích thước màn hình
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Tính toán vị trí để cửa sổ ở giữa màn hình
    x_pos = (screen_width // 2) - (width // 2)
    y_pos = (screen_height // 2) - (height // 2)

    window.destroy()
    
    return(f"{width}x{height}+{x_pos}+{y_pos}")

def AI_generate_content(prompt, file, isPNG) ->str:
    '''Hàm khởi tạo và truy cập AI, hết hạn mức sẽ đổi key khác 
    prompt: câu lệnh yêu cầu AI thực thi
    file: file để gửi cho AI
    isPNG: true: file ảnh, false: file pdf
    '''
    global api_key
    if not api_key:
        api_key = config_file_value('API key')

    while True: 
        try:
            global key_count 
            if key_count == len(api_key):
                return ''
            
            model = genai.GenerativeModel(model_name=GE_MODEL)

            genai.configure(api_key=api_key[key_count])

            if file == None:
                return model.generate_content(prompt).text
            else: 
                if isPNG:
                    with PIL.Image.open(file) as image_file:
                        return model.generate_content([prompt, image_file]).text
                else:
                    return model.generate_content([prompt, genai.upload_file(file)]).text
                break
        except Exception as e:
            # messagebox.showerror("Lỗi AI_generate_content", f'hết key {key_count}')
            # window.iconify()
            key_count += 1
            # return  # Thoát khỏi hàm ngay lập tức, không thực hiện các dòng mã sau

def find_firefox_executable():
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

def initialize_web_driver(window, label):
    def show_webdriver_error_dialog():
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
        open_button = ttk.Button(button_frame, text="Mở Web", command=open_website) # Đổi tên và chức năng

        ok_button.pack(side="right", padx=(10, 0))
        open_button.pack(side="right") # Đặt nút Mở Web vào

        # --- Căn giữa và hiển thị cửa sổ ---
        dialog.update_idletasks()
        dialog.geometry(window_center_position(dialog.winfo_width(), dialog.winfo_height()))

        dialog.transient()
        dialog.grab_set()
        dialog.focus_set()
        dialog.wait_window()

    """
    Hàm khởi tạo chính, thử tất cả các phương pháp theo thứ tự ưu tiên.
    """
    print("--- Bắt đầu quy trình khởi tạo WebDriver ---")

    update_label(window,label,'\n Khởi tạo Edge (manual):')
    # 1. Sử dụng file msedgedriver.exe cục bộ
    try:
        print("▶️ [1/4] Thử tìm file msedgedriver.exe cục bộ...")

        found_path = find_file( 'msedgedriver.exe')

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


        release_info= check_for_updates(driver_ver,'Hung-ccan1920/msedgedriver')

        if release_info:
            perform_update(release_info['release_info'],'msedgedriver.exe',False)

        # Tìm lại 
        found_path = find_file( 'msedgedriver.exe')

        service = EdgeService(executable_path=found_path)
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Edge(service=service, options=options)
        update_label(window,label,' Thành công!')
        print("✅ Thành công! Sử dụng Edge từ file cục bộ.")
        return driver
    except Exception as e:
        print(f"⚠️ Thất bại với file Edge cục bộ: {e}")

    update_label(window,label,' Thất bại!')
    update_label(window,label,'\n Khởi tạo Edge (automatic):')

    # 2. Thử Edge tự động
    try:
        print("▶️ [2/4] Thử khởi tạo Edge tự động...")
        service = EdgeService(EdgeChromiumDriverManager().install())
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Edge(service=service, options=options)
        update_label(window,label,' Thành công!')
        print("✅ Thành công! Sử dụng Microsoft Edge.")
        return driver
    except Exception as e:
        print(f"⚠️ Thất bại với Edge: {e}")

    update_label(window,label,' Thất bại!')
    update_label(window,label,'\n Khởi tạo Chrome:')
    # 3. Thử Chrome tự động
    try:
        print("▶️ [3/4] Thử khởi tạo Chrome tự động...")
        service = ChromeService(ChromeDriverManager().install())
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=service, options=options)
        update_label(window,label,' Thành công!')
        print("✅ Thành công! Sử dụng Google Chrome.")
        return driver
    except Exception as e:
        print(f"⚠️ Thất bại với Chrome: {e}")

    update_label(window,label,' Thất bại!')
    update_label(window,label,'\n Khởi tạo Firefox:')

    # 4. Thử Firefox tự động (với logic tìm kiếm tối ưu)
    try:
        print("▶️ [4/4] Thử khởi tạo Firefox...")
        options = FirefoxOptions()
        options.add_argument("--start-maximized")
        service = None
        
        # 4.1 Thử cách tự động đơn giản nhất
        print("   -> Thử tìm Firefox tự động (cách tiêu chuẩn)...")
        try:
            service = FirefoxService(GeckoDriverManager().install())      
            driver = webdriver.Firefox(service=service, options=options)
            return driver
        except Exception:
            # 4.2 Nếu lỗi, mới dùng đến hàm tìm kiếm nâng cao
            print("   -> Tìm kiếm tiêu chuẩn thất bại. Thử tìm kiếm nâng cao...")
            firefox_path = find_firefox_executable()
            if not firefox_path:
                raise ValueError("Không thể tự động tìm thấy nơi cài đặt Firefox.")
            
            print(f"   -> Đã tìm thấy Firefox tại: {firefox_path}")
            options.binary_location = firefox_path
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
            update_label(window,label,' Thành công!')
            print("✅ Thành công! Sử dụng Firefox.")
            return driver
    except Exception as e:
        print(f"⚠️ Thất bại với Firefox: {e}")

    # Tất cả đều thất bại, hiển thị thông báo lỗi
    update_label(window,label,' Thất bại!')
    print("❌ Mọi phương pháp đều thất bại. Hiển thị thông báo cho người dùng.")
    show_webdriver_error_dialog()
    return None

def web_write (edge_driver, element_by, address, value):
    '''
    Find and write value to web element
    element_by: By.XPATH or By.CSS_SELECTOR
    '''
    try:
        web_element = edge_driver.find_element(element_by, address)
        web_element.send_keys(value)
    except Exception as e:
        messagebox.showerror("loi", e)
        None

def XML_file_read(file_name, isuseAI)->defaultdict:
    ''' Đọc file XML và truy xuất giá trị, trả về thông tin hóa đơn
    Args:
        file_name: Đường dẫn đến file xml.
        isuseAI: sử dụng AI để tìm thông tin hợp đồng không?'''
    
    # Phân tích cú pháp file XML
    tree = etree.parse(file_name)
    root = tree.getroot()
    thong_tin = defaultdict()

    # Tìm thẻ <TTChung>
    xml_data = tree.xpath('/HDon/DLHDon/TTChung')[0]
    # Lấy thông tin TTChung
    thong_tin['KHHDon'] = xml_data.find('KHHDon').text
    thong_tin['SHDon'] = xml_data.find('SHDon').text
    thong_tin['NLap'] = xml_data.find('NLap').text

    # Tìm thẻ <TToan> 
    xml_data = tree.xpath('/HDon/DLHDon/NDHDon/TToan')[0]
     # Lấy thông tin thanh toan

# Danh sách các thẻ cần xử lý
    keys_to_process = ['TgTThue', 'TgTTTBSo', 'TgTCThue']

    for key in keys_to_process:
        # Tìm thẻ tương ứng với key
        element = xml_data.find(key)
        # Kiểm tra xem thẻ có tồn tại không, sau đó mới dùng walrus operator
        if element is not None and (text_value := element.text):
            thong_tin[key] = int(float(text_value))

    # Tìm thẻ <NBan>
    xml_data = tree.xpath('/HDon/DLHDon/NDHDon/NBan')[0]
    # Lấy thông tin NBan
    thong_tin['Ten'] = xml_data.find('Ten').text
    thong_tin['MST'] = xml_data.find('MST').text

    # thông tin tên gói và hợp đồng
    # lấy nội dung hóa đơn
    contract_info = tree.xpath('/HDon/DLHDon/NDHDon/DSHHDVu/HHDVu/THHDVu')[0].text
    
    if isuseAI:
        response = AI_generate_content(f'Tìm kiếm thông tin trong nội dung hóa đơn sau: {contract_info} '
                                'và trả về thông tin theo từng dòng các nội dung sau: '
                                'Số hợp đồng: [giá trị]'
                                'Ngày hợp đồng: [giá trị]'
                                'Tên gói : [giá trị].'
                                'Qui tắc:'
                                '- Chỉ trả về 3 dòng thông tin như trên. Không thêm lời chào, giải thích, ghi chú hay bất kỳ ký tự thừa nào. Giá trị nào không có thì để chuỗi rỗng'
                                '- chuyển đổi ngày tháng sang định dạng dd/MM/yyyy'
                                '- Số hợp đồng: trong nội dung hóa đơn, ví dụ 406/HD-TTMLMN'
                                '- Tên gói: bước 1: tìm loại hình công việc trong phần nội dung hóa đơn, chuyển thành mã viết tắt: nếu có nội dung tư vấn thiết kế hoặc lập phương án thì thêm mã TVTK, tư vấn thẩm tra thì thêm mã TVTT, giám sát thì thêm mã TVGS, sữa chữa thì thêm mã SCCT, thi công thì thêm mã TC. Bước 2: tìm mã gói thầu đi kèm (thường có chuỗi ký tự và số, ví dụ 24BDCF-TA). Bước 3 kết hợp lại theo quy tắc [Mã viết tắt] [Mã gói thầu] (ví dụ SCCT 24BDCF-TA)',
                                None,
                                False)
        if response == '':
            messagebox.showerror('Lỗi PDF_file_read', 'Hết hạn mức')
            return {}

        # xóa ký tự `
        response = response.replace('`','')

        i = 0
        key= ['SHDong', 'NHDong', 'Goi']
        # Xử lý từng dòng
        for line in response.split('\n'):  # Tách chuỗi thành các dòng
            if line != '':    
                value = line.split(':', 1)[1].strip()  # Tách dòng lấy phần phía sau dấu :
                thong_tin[key[i]] = value.strip()  # Lưu vào defaultdict (loại bỏ khoảng trắng)
                i += 1

        # Xử lý ngày:
        if thong_tin['NHDong']!= '':
            thong_tin['NHDong'] = datetime.strptime(thong_tin['NHDong'], "%d/%m/%Y").strftime("%Y/%m/%d")

    # # Loại bỏ phần phụ lục khỏi chuỗi, xử lý cả "phụ lục" và "Phụ lục"
    # contract_info = re.sub(r", (phụ|Phụ) lục.*", "", contract_info, flags=re.IGNORECASE)

    #  # Sử dụng regular expression để tìm số hợp đồng (bao gồm cả "HĐ")
    # so_hop_dong_match = re.search(r"(?:HĐ số|hợp đồng số:)\s*(\d+\/[\w\.-]+)", contract_info)
    # thong_tin['SHDong'] = so_hop_dong_match.group(1) if so_hop_dong_match else 'None'

    # # Sử dụng regular expression để tìm ngày hợp đồng
    # ngay_hop_dong_match = re.search(r"ngày (\d{2}/\d{2}/\d{4})", contract_info)
    
    # if ngay_hop_dong_match:
    #     HD_date = datetime.strptime(ngay_hop_dong_match.group(1), "%d/%m/%Y").strftime("%Y/%m/%d")
    # else:
    #     HD_date = 'None'

    # thong_tin['NHDong'] = HD_date

    # # Tìm loại công việc dựa vào từ khóa
    # loai_cong_viec = 'None'
    # if "khảo sát" in contract_info.lower() or "thiết kế" in contract_info.lower() or "tư vấn thiết kế" in contract_info.lower():
    #     loai_cong_viec = "TVTK"
    # if "thẩm tra" in contract_info.lower():
    #     loai_cong_viec = "TVTT"
    # if "giám sát" in contract_info.lower():
    #     loai_cong_viec = "TVGS"
    # if "sửa chữa" in contract_info.lower() or "sữa chữa" in contract_info.lower():
    #     loai_cong_viec = "SCCT"
    # if "thi công" in contract_info.lower():
    #    loai_cong_viec = "TC"

    # # Sử dụng regular expression để tìm chuỗi đặc biệt
    # chuoi_dac_biet_match = re.search(r"(\d{2}[A-Z]{2,}[A-Z\d-]{2,})", contract_info)
    # chuoi_dac_biet = chuoi_dac_biet_match.group(1) if chuoi_dac_biet_match else 'None'

    # thong_tin['Goi'] = f'{loai_cong_viec} {chuoi_dac_biet}'

        thong_tin['LinkTC']= ''
        thong_tin['MaTC']= ''

    return thong_tin

def PDF_file_read(file_name)->defaultdict:
    ''' Đọc file PDF và truy xuất giá trị, trả về thông tin hóa đơn''' 

    # Chuyển file PDF thành hình ảnh để gửi Gemini phân tích
    #Mở file PDF
    with fitz.open(file_name) as doc:

        # Lấy trang đầu tiên (chỉ số trang bắt đầu từ 0)
        page = doc.load_page(0)

        # Chuyển trang thành hình ảnh (độ phân giải 150 DPI)
        pix = page.get_pixmap(dpi=150)

        # Lưu hình ảnh trang đầu tiên
        pix.save('pdf.png')

    
    # response = AI_generate_content('Truy xuất thông tin từ hình ảnh và chỉ trả về cho tôi thông tin theo từng dòng các thông tin sau: '
    #                         'Người bán: [giá trị]'
    #                         'Mã số thuế người bán: [giá trị]'
    #                         'Ngày hóa đơn (định dạng dd/MM/yyyy): [giá trị]'
    #                         'Ký hiệu: [giá trị]'
    #                         'Số: [giá trị]'
    #                         'Số tiền chưa thuế: [giá trị]'
    #                         'Số tiền thuế: [giá trị]'
    #                         'Số tiền sau thuế: [giá trị]'
    #                         'Link tra cứu hóa đơn: [giá trị]'
    #                         'Mã bí mật tra cứu: [giá trị]'
    #                         'Số hợp đồng (trong nội dung hóa đơn, ví dụ 406/HD-TTMLMN): [giá trị]'
    #                         'Ngày hợp đồng (định dạng dd/MM/yyyy): [giá trị]'
    #                         'Tên gói : [giá trị].'
    #                         'Lưu ý chổ tên gói: chỉ lấy từ viết tắt của gói, và thêm vào mã phía trước tên gói nếu trong nội dung hóa dơn có từ khảo sát thiết kế thì thêm mã TVTK, thẩm tra thì thêm mã TVTT, giám sát thì thêm mã TVGS, sữa chữa thì thêm mã SCCT, thi công thì thêm mã TC, Ví du: SCCT 24BDCF-TA'
    #                         'Lưu ý: số tiền có thể là số âm, nếu dòng nào không tìm được thì vẫn trả kết quả chuỗi rỗng, không thêm bất cứ ký tự gì ngoài cú pháp trên',
    #                         'pdf.png',
    #                         True)

    response = AI_generate_content('Bạn là một trợ lý AI chuyên về xử lý và trích xuất dữ liệu từ hình ảnh hóa đơn điện tử của Việt Nam, Bạn phân tích hình ảnh hóa đơn được cung cấp và trả về thông tin một cách chính xác theo đúng định dạng và các quy tắc được nêu dưới đây: '
                            'Người bán: [giá trị]'
                            'Mã số thuế người bán: [giá trị]'
                            'Ngày hóa đơn: [giá trị]'
                            'Ký hiệu: [giá trị]'
                            'Số: [giá trị]'
                            'Số tiền chưa thuế: [giá trị]'
                            'Số tiền thuế: [giá trị]'
                            'Số tiền sau thuế: [giá trị]'
                            'Link tra cứu hóa đơn: [giá trị]'
                            'Mã tra cứu hoặc mã nhận hóa đơn: [giá trị]'
                            'Số hợp đồng: [giá trị]'
                            'Ngày hợp đồng: [giá trị]'
                            'Tên gói : [giá trị].'
                            'Qui tắc:'
                            '- Chỉ trả về 13 dòng thông tin như trên. Không thêm lời chào, giải thích, ghi chú hay bất kỳ ký tự thừa nào. Giá trị nào không có thì để chuỗi rỗng'
                            '- số tiền có thể là số âm, giữ nguyên dấu'
                            '- chuyển đổi ngày tháng sang định dạng dd/MM/yyyy'
                            '- Số hợp đồng: trong nội dung hóa đơn, ví dụ 406/HD-TTMLMN'
                            '- Tên gói: trích xuất nội dung hóa đơn trong phần tên hàng hóa, dịch vụ (thường ở phía đầu, tránh nhầm lẫn với tên công việc), bước 1: tìm loại hình công việc trong phần nội dung hóa đơn, chuyển thành mã viết tắt: nếu có nội dung tư vấn thiết kế hoặc tư vấn lập phương án thì thêm mã TVTK, tư vấn thẩm tra thì thêm mã TVTT, giám sát thì thêm mã TVGS, sữa chữa thì thêm mã SCCT, thi công thì thêm mã TC. Bước 2: tìm mã gói thầu đi kèm (thường có chuỗi ký tự và số, ví dụ 24BDCF-TA). Bước 3 kết hợp lại theo quy tắc [Mã viết tắt] [Mã gói thầu] (ví dụ SCCT 24BDCF-TA)',
                            'pdf.png',
                            True)
    if response == '':
        messagebox.showerror('Lỗi PDF_file_read', 'Hết hạn mức')
        return {}

    # xóa ký tự `
    response = response.replace('`','')

    i = 0
    thong_tin = defaultdict()
    key= ['Ten','MST', 'NLap', 'KHHDon', 'SHDon','TgTCThue', 'TgTThue', 'TgTTTBSo', 'LinkTC', 'MaTC', 'SHDong', 'NHDong', 'Goi']
    # Xử lý từng dòng
    for line in response.split('\n'):  # Tách chuỗi thành các dòng
        if line != '':    
            value = line.split(':', 1)[1].strip()  # Tách dòng lấy phần phía sau dấu :
            thong_tin[key[i]] = value.strip()  # Lưu vào defaultdict (loại bỏ khoảng trắng)
            i += 1

    # Bỏ số 1 ở ký hiệu hóa đơn
    thong_tin['KHHDon'] = thong_tin['KHHDon'][1:]

    # Xử lý số
    # Danh sách các key cần xử lý số
    numeric_keys = ['TgTThue', 'TgTTTBSo', 'TgTCThue']

    for key in numeric_keys:
        # Dùng .get(key) để tránh lỗi nếu key không tồn tại
        value = thong_tin.get(key)
        
        # Kiểm tra xem giá trị có tồn tại và không rỗng không
        if value:
            # Thực hiện chuyển đổi và gán lại giá trị
            cleaned_value = str(value).replace('.', '').replace(',', '.')
            thong_tin[key] = int(float(cleaned_value))

    # Xử lý ngày:
    if thong_tin['NHDong']:
        thong_tin['NHDong'] = datetime.strptime(thong_tin['NHDong'], "%d/%m/%Y").strftime("%Y/%m/%d")
    thong_tin['NLap'] = datetime.strptime(thong_tin['NLap'], "%d/%m/%Y").strftime("%Y/%m/%d")

    return thong_tin

def update_label(window, label, new_text, append=True):
  """Cập nhật nội dung của một đối tượng Label.

  Args:
      window: Cửa sổ chính để cập nhật giao diện (window.update_idletasks).
      label: Đối tượng label cần cập nhật.
      new_text: Nội dung mới để hiển thị.
      append (bool): Nếu True, nội dung mới sẽ được nối vào nội dung cũ.
                     Nếu False, nội dung cũ sẽ bị xóa và thay thế bằng nội dung mới.
                     Mặc định là True.
  """
  if append:
    # Nối nội dung mới vào nội dung hiện tại
    current_text = label.cget("text")
    updated_text = current_text + new_text
    label.config(text=updated_text)
  else:
    # Thay thế hoàn toàn nội dung cũ
    label.config(text=new_text)
  
  window.update_idletasks()

def to_time_from_df(value):
    date_obj = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
    return date_obj.strftime("%d/%m/%Y")

def find_xml_file(pdf_file_path, pdf_info ):
    """
    Tìm file XML tương ứng với file PDF.

    Args:
        pdf_file_path: Đường dẫn đến file PDF.

    Returns:
        str: Đường dẫn đến file XML, hoặc chuỗi rỗng nếu không tìm thấy.
    """
    try:
        # Tìm file XML theo tên file
        xml_file_path = find_xml_file_by_name(pdf_file_path)
        if xml_file_path:
            return xml_file_path

        # Nếu không tìm thấy theo tên, tìm theo nội dung
        return find_xml_file_by_content(pdf_file_path, pdf_info)

    except Exception as e:
        print(f"Error finding XML file: {e}")
        return ""

def find_xml_file_by_name(pdf_file_path):
    """Tìm file XML theo tên file."""
    try:
        pdf_file_name = os.path.splitext(os.path.basename(pdf_file_path))[0]
        pdf_dir = os.path.dirname(pdf_file_path)
        xml_file_path = glob.glob(os.path.join(pdf_dir, f"{pdf_file_name}*.xml"))
        if xml_file_path:
            return xml_file_path[0].replace("/", "\\")
        return ""
    except Exception as e:
        print(f"Error finding XML file by name: {e}")
        return ""

def find_xml_file_by_content(pdf_file_path, pdf_info):
    """Tìm file XML theo nội dung."""
    try:
        # Lấy thư mục chứa file PDF
        pdf_dir = os.path.dirname(pdf_file_path)

        # Tìm tất cả các file XML trong thư mục và thư mục con
        for xml_file in glob.glob(os.path.join(pdf_dir, "**/*.xml"), recursive=True):
            try:
                tree = etree.parse(xml_file)
                xml_data = tree.xpath('/HDon/DLHDon/TTChung')[0]

                # So sánh thông tin
                if (xml_data.find('KHHDon').text == pdf_info['KHHDon'] and
                    xml_data.find('SHDon').text == pdf_info['SHDon']):
                    return xml_file.replace("/", "\\")
            except Exception as e:
                print(f"Error processing XML file {xml_file}: {e}")
                
        return ""  # Không tìm thấy file XML phù hợp

    except Exception as e:
        print(f"Error finding XML file by content: {e}")
        return ""
def find_file(file_name):
    """Tìm kiếm một file trong thư mục gốc của ứng dụng và các thư mục con.
    Trả về đường dẫn đầy đủ nếu tìm thấy, ngược lại trả về None.
    """
    app_dir = get_app_path()
    
    file_path = None
    for root, dirs, files in os.walk(app_dir):
        if file_name in files:
            file_path = os.path.join(root, file_name)
            break
    return file_path

def get_app_path():
    """Trả về đường dẫn đến thư mục chứa ứng dụng."""
    if getattr(sys, 'frozen', False):
        # Nếu đang chạy từ file .exe
        return os.path.dirname(sys.executable)
    else:
        # Nếu đang chạy từ file .py
        return os.path.dirname(os.path.realpath(__file__))