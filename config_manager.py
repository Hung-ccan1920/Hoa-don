import os
import sys
import json
import tempfile
import shutil
from dotenv import load_dotenv, set_key

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
import base64
    
# ==============================================================================
# CONFIGURATION MANAGER CLASS
# ==============================================================================

class ConfigManager:
    """
    Lớp quản lý cấu hình "tất cả trong một":
    - Quản lý file config.json và .env.
    - Tự động mã hóa/giải mã các trường được đánh dấu.
    - Tích hợp sẵn giao diện thiết lập ban đầu.
    """
    CONFIG_SCHEMA = {
        'excel_path': {
            'storage': 'json', 
            'default': '', 
            'required': True, 
            'label': 'Excel File',
            'type': '*.xlsx *.xls *.xlsm'
        },
        'API_KEY': {
            'storage': 'env', 
            'default': None, 
            'required': True, 
            'label': 'API Key'
        },
        'COMPANY_USERNAME': {
            'storage': 'env', 
            'default': None, 
            'required': False, 
            'label': 'Username'
        },
        'COMPANY_PASSWORD': {
            'storage': 'env', 
            'default': None, 
            'required': False, 
            'label': 'Password',
            'encrypt': True
        }
    }

    # --- CÁC HẰNG SỐ MÃ HÓA ---
    _CAESAR_KEY = 9
    _ENCRYPTION_MARKER = "ENC"

    def __init__(self, app_name="ChuyenTriHoaDon"):
        self.APP_NAME = app_name
        self._app_data_dir = os.path.join(os.getenv('APPDATA'), self.APP_NAME)
        self._config_path = os.path.join(self._app_data_dir, 'config.json')
        self._root_dir = self._get_root_dir()
        self._dotenv_path = os.path.join(self._root_dir, '.env')
        self._temp_dir = os.path.join(tempfile.gettempdir(), self.APP_NAME)

        self.config = {}
        self.secrets = {}

        self._ensure_dirs_exist()
        self._load_all_configs()

    def _get_root_dir(self):
        if getattr(sys, 'frozen', False): return os.path.dirname(sys.executable)
        else: return os.path.dirname(os.path.abspath(sys.argv[0]))

    def _ensure_dirs_exist(self):
        os.makedirs(self._app_data_dir, exist_ok=True)
        os.makedirs(self._temp_dir, exist_ok=True)

    def _load_all_configs(self):
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            json_data = {}
        
        load_dotenv(dotenv_path=self._dotenv_path)

        for key, props in self.CONFIG_SCHEMA.items():
            if props['storage'] == 'json':
                self.config[key] = json_data.get(key, props['default'])
            elif props['storage'] == 'env':
                self.secrets[key] = os.getenv(key)
        
        self.save_config()

    def save_config(self):
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def save_secret(self, key, value):
        """Tự động mã hóa các trường được đánh dấu 'encrypt': True."""
        props = self.CONFIG_SCHEMA.get(key)
        final_value = value

        # Tự động mã hóa nếu cần
        if props and props.get('encrypt'):
            final_value = self._encrypt_password(value)

        set_key(self._dotenv_path, key, final_value or '')
        self.secrets[key] = final_value

    def get(self, key, default=None):
        props = self.CONFIG_SCHEMA.get(key)
        if not props: return default
        
        value = None
        if props['storage'] == 'json': value = self.config.get(key, default)
        elif props['storage'] == 'env': value = self.secrets.get(key, default)

        # Tự động giải mã nếu cần
        if props.get('encrypt') and value:
            return self._decrypt_password(value)
        return value
    
    def get_temp_file_path(self, filename):
        return os.path.join(self._temp_dir, filename)

    def cleanup_temp_dir(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)
            print(f"Cleaned up temporary directory: {self._temp_dir}")

    def check_and_prompt_for_missing(self):
        missing_keys = [key for key, props in self.CONFIG_SCHEMA.items() if props['required'] and not self.get(key)]

        if missing_keys:
            print(f"Detected missing required configuration: {missing_keys}")
            self._prompt_for_values(missing_keys)

    def _prompt_for_values(self, keys_to_ask):
        window = tk.Tk()
        window.title("Initial Setup")
        window.config(bg="#2e2e2e")
        window.resizable(False, False)
        window.attributes('-topmost', True)
        
        height = 100 + len(keys_to_ask) * 40
        width = 450
        self.center_window(window, width, height)
        # screen_width = window.winfo_screenwidth()
        # screen_height = window.winfo_screenheight()
        # x_pos = (screen_width // 2) - (width // 2)
        # y_pos = (screen_height // 2) - (height // 2)
        # window.geometry(f"{width}{"x"}{height}+{x_pos}+{y_pos}")

        def on_closing():
            if messagebox.askyesno("Confirm Exit", "The application cannot run with missing information.\nAre you sure you want to exit?", parent=window):
                window.destroy()
                sys.exit()
        window.protocol("WM_DELETE_WINDOW", on_closing)

        style = ttk.Style(window)
        style.theme_use("clam")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("Dark.TButton", background="#444444", foreground="white", font=("Arial", 10, "bold"), borderwidth=2, padding=10, relief="raised")
        style.map("Dark.TButton", background=[("active", "#555555")], relief=[("pressed", "sunken")])
        style.configure("Small.TButton", font=("Arial", 8, "bold"), padding=(2, 2))
        style.map("Small.TButton", background=[("active", "#555555"), ('!disabled', '#444444')], foreground=[('!disabled', 'white')], relief=[("pressed", "sunken")])
        
        entry_widgets = {}

        def save_values():
            for key, entry in entry_widgets.items():
                if not entry.get().strip():
                    label = self.CONFIG_SCHEMA[key]['label']
                    messagebox.showwarning("Warning", f"The value for '{label}' cannot be empty.", parent=window)
                    return
            
            for key, entry in entry_widgets.items():
                value = entry.get().strip()
                storage_type = self.CONFIG_SCHEMA[key]['storage']
                if storage_type == 'json': self.config[key] = value
                else: self.save_secret(key, value)
            
            self.save_config()
            # messagebox.showinfo("Success", "Configuration saved successfully! Please restart the application.", parent=window)
            window.destroy()
            # sys.exit()

        tk.Label(window, text="Please provide the required information:", fg="white", bg="#2e2e2e", font=("Arial", 12)).pack(pady=(10, 5))

        for key in keys_to_ask:
            props = self.CONFIG_SCHEMA[key]
            frame = ttk.Frame(window, style="TFrame")
            frame.pack(pady=5, fill="x", padx=15)
            tk.Label(frame, text=f"{props['label']}:", fg="white", bg="#2e2e2e", font=("Arial", 10), width=15, anchor="w").pack(side="left")

            entry = tk.Entry(frame, font=("Arial", 10), bg="#555555", fg="white", insertbackground="white", relief="solid", borderwidth=1)
            
            if 'path' in key:
                choose_button = ttk.Button(frame, text="...", style="Small.TButton", width=3, command=lambda e=entry, t = props['type']: self._choose_file(e, t))
                choose_button.pack(side="right", padx=(5, 0))
            elif key == 'API_KEY':
                guide_button = ttk.Button(frame, text="?", style="Small.TButton", width=3, command=self._open_api_guide)
                guide_button.pack(side="right", padx=(5, 0))

            entry.pack(side="left", expand=True, fill="x")
            entry_widgets[key] = entry
        
        ttk.Button(window, text="Save", style="Dark.TButton", command=save_values).pack(pady=10)
        window.mainloop()

    def _choose_file(self, entry_widget, file_types):
        file_path = filedialog.askopenfilename(title="Select File", filetypes=[("Files", file_types)])
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
            
    def _open_api_guide(self):
        video_path = os.path.join(self._root_dir, "Get API key.mp4")
        if os.path.exists(video_path): webbrowser.open(video_path)
        else: messagebox.showwarning("Not Found", "File 'Get API key.mp4' was not found.")
        
    # --- LOGIC MÃ HÓA (Chuyển từ password_manager.py vào thành phương thức private) ---
    def _caesar_cipher(self, text, decrypt=False):
        result = []
        for char in text:
            if 'a' <= char <= 'z':
                start = ord('a')
                offset = (ord(char) - start + (self._CAESAR_KEY if not decrypt else -self._CAESAR_KEY)) % 26
                shifted_char = chr(start + offset)
            elif 'A' <= char <= 'Z':
                start = ord('A')
                offset = (ord(char) - start + (self._CAESAR_KEY if not decrypt else -self._CAESAR_KEY)) % 26
                shifted_char = chr(start + offset)
            elif '0' <= char <= '9':
                start = ord('0')
                offset = (ord(char) - start + (self._CAESAR_KEY if not decrypt else -self._CAESAR_KEY)) % 10
                shifted_char = chr(start + offset)
            else:
                shifted_char = char
            result.append(shifted_char)
        return "".join(result)

    def _encrypt_password(self, password):
        if not password or password.startswith(self._ENCRYPTION_MARKER): return password
        caesar_encrypted = self._caesar_cipher(password)
        base64_encrypted = base64.b64encode(caesar_encrypted.encode('utf-8')).decode('utf-8')
        return self._ENCRYPTION_MARKER + base64_encrypted

    def _decrypt_password(self, encrypted_password):
        if not encrypted_password or not encrypted_password.startswith(self._ENCRYPTION_MARKER):
            return encrypted_password
        actual_password = encrypted_password[len(self._ENCRYPTION_MARKER):]
        try:
            base64_decoded = base64.b64decode(actual_password.encode('utf-8')).decode('utf-8')
            return self._caesar_cipher(base64_decoded, decrypt=True)
        except Exception as e:
            print(f"Decryption Error: {e}")
            return encrypted_password
        
    def center_window(self, window, width, height):
        """Canh giữa một cửa sổ (Tk hoặc Toplevel) trên màn hình."""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x_pos = (screen_width // 2) - (width // 2)
        y_pos = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}{"x"}{height}+{x_pos}+{y_pos}")
# ==============================================================================
# SETTINGS WINDOW CLASS (for use when the main app is running)
# ==============================================================================

class SettingsWindow(tk.Toplevel):
    """Cửa sổ cài đặt chuyên nghiệp, cho phép chỉnh sửa cấu hình."""
    def __init__(self, master, config_manager):
        super().__init__(master)
        self.config_manager = config_manager
        self.title("Settings")
        self.config(bg="#2e2e2e")
        self.resizable(False, False)

        # Canh giữa màn hình
        num_keys = len(self.config_manager.CONFIG_SCHEMA)
        height = 100 + (num_keys * 40)
        width = 450
        self.config_manager.center_window(self, width, height)

        self.transient(master)
        self.grab_set()
        self._setup_styles()
        self._create_widgets()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TCheckbutton", background="#2e2e2e", foreground="white", font=("Arial", 9))
        style.map("TCheckbutton", background=[("active", "#3c3c3c")], indicatorcolor=[('selected', '#66b3ff'), ('!selected', 'white')])
        style.configure("Dark.TButton", background="#444444", foreground="white", font=("Arial", 10, "bold"), borderwidth=2, padding=10, relief="raised")
        style.map("Dark.TButton", background=[("active", "#555555")], relief=[("pressed", "sunken")])
        style.configure("Small.TButton", font=("Arial", 8, "bold"), padding=(2, 2))
        style.map("Small.TButton", background=[("active", "#555555"), ('!disabled', '#444444')], foreground=[('!disabled', 'white')], relief=[("pressed", "sunken")])

    def _create_widgets(self):
        """Tạo và sắp xếp các widget trên cửa sổ bằng grid một cách nhất quán."""
        self.entry_widgets = {}
        
        # Cấu hình grid cho cửa sổ chính (self)
        self.columnconfigure(0, weight=1)

        # Hàng 0: Tiêu đề chính
        tk.Label(self, text="Configuration Settings:", fg="white", bg="#2e2e2e", font=("Arial", 12)).grid(row=0, column=0, pady=(10, 5), padx=15, sticky="w")

        # Bắt đầu từ hàng 1 để tạo các dòng cài đặt
        row_index = 1
        for key, props in self.config_manager.CONFIG_SCHEMA.items():
            frame = ttk.Frame(self, style="TFrame")
            # Mỗi frame là một hàng trong grid của cửa sổ chính
            frame.grid(row=row_index, column=0, sticky="ew", padx=15, pady=5)
            
            # Cấu hình grid cho nội dung bên trong frame
            frame.columnconfigure(1, weight=1) # Cột 1 (Entry) sẽ co giãn

            # Cột 0: Nhãn (Label)
            tk.Label(frame, text=f"{props['label']}:", fg="white", bg="#2e2e2e", font=("Arial", 10), width=15, anchor="w").grid(row=0, column=0, sticky="w")

            # Logic tạo Entry
            if props.get('encrypt'):
                entry = PasswordEntry(frame, font=("Arial", 10), bg="#555555", fg="white", insertbackground="white", relief="solid", borderwidth=1)
                current_value = self.config_manager.get(key)
                if current_value:
                    entry.set_real_text(current_value)
                entry.bind("<KeyRelease>", self._on_password_edit)
            else:
                entry = tk.Entry(frame, font=("Arial", 10), bg="#555555", fg="white", insertbackground="white", relief="solid", borderwidth=1)
                current_value = self.config_manager.get(key)
                if current_value:
                    entry.insert(0, current_value)
            
            # Cột 1: Ô nhập liệu (Entry)
            entry.grid(row=0, column=1, sticky="ew")
            self.entry_widgets[key] = entry

            # Cột 2: Các nút phụ
            if 'type' in props: 
                ttk.Button(frame, text="...", style="Small.TButton", width=3, command=lambda e=entry, t=props['type']: self.config_manager._choose_file(e, t)).grid(row=0, column=2, sticky="e", padx=(5,0))
            elif key == 'API_KEY':
                ttk.Button(frame, text="?", style="Small.TButton", width=3, command=self.config_manager._open_api_guide).grid(row=0, column=2, sticky="e", padx=(5,0))
            elif props.get('encrypt'):
                ttk.Button(frame, text="⚯", style="Small.TButton", width=3, command=lambda e=entry: e.toggle_visibility()).grid(row=0, column=2, sticky="e", padx=(5,0))

            row_index += 1
        
        # Hàng cuối: Nút Save và Cancel
        button_frame = ttk.Frame(self, style="TFrame")
        button_frame.grid(row=row_index, column=0, pady=20)
        ttk.Button(button_frame, text="Save", style="Dark.TButton", command=self._save_values).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", style="Dark.TButton", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _on_password_edit(self, event=None):
        """Hàm này được gọi khi người dùng gõ vào ô mật khẩu."""
        self.password_is_edited = True

    def _save_values(self):
        initial_password = self.config_manager.get('PASSWORD')
        """Lưu lại các giá trị đã thay đổi."""
        for key, entry in self.entry_widgets.items():
            props = self.config_manager.CONFIG_SCHEMA[key]
            value = ""

            # Lấy giá trị từ widget
            if isinstance(entry, PasswordEntry):
                value = entry.get_real_text()
                # Chỉ lưu nếu mật khẩu mới khác mật khẩu ban đầu
                if value == initial_password:
                    continue # Bỏ qua, không lưu
            else:
                value = entry.get().strip()

            # Kiểm tra các trường bắt buộc
            if props['required'] and not value:
                messagebox.showwarning("Missing Information", f"Value for '{props['label']}' cannot be empty.", parent=self)
                return
            
            # Lưu giá trị
            if props['storage'] == 'json':
                self.config_manager.config[key] = value
            else: # storage == 'env'
                self.config_manager.save_secret(key, value)
        
        self.config_manager.save_config()
        # messagebox.showinfo("Success", "Changes saved!", parent=self)
        self.destroy()


class PasswordEntry(tk.Entry):
    def __init__(self, master=None, **kwargs):
        self._real_text = ""
        self._is_syncing = False
        self._is_hidden = True # Trạng thái nội bộ: mặc định là ẩn
        
        self.sv = tk.StringVar()
        self.sv.trace_add("write", self._sync_content)
        
        # Luôn khởi tạo với show='*'
        super().__init__(master, textvariable=self.sv, show='*', **kwargs)

    def _sync_content(self, *args):
        """Hàm "bộ não" được gọi mỗi khi StringVar thay đổi."""
        if self._is_syncing:
            return

        displayed_text = self.sv.get()
        cursor_pos = self.index(tk.INSERT)

        # Logic suy luận thay đổi và cập nhật _real_text
        if self._is_hidden: # Nếu đang ở chế độ ẩn (hiển thị ***)
            if len(displayed_text) < len(self._real_text):
                self._real_text = self._real_text[:cursor_pos] + self._real_text[cursor_pos + (len(self._real_text) - len(displayed_text)):]
            elif len(displayed_text) > len(self._real_text):
                added_text = displayed_text[cursor_pos - (len(displayed_text) - len(self._real_text)) : cursor_pos]
                self._real_text = self._real_text[:cursor_pos - len(added_text)] + added_text + self._real_text[cursor_pos - len(added_text):]
        else: # Nếu đang ở chế độ hiện (hiển thị text thật)
            self._real_text = displayed_text

        # Cập nhật lại giao diện cho đúng với trạng thái hiện tại
        self.update_display()
        self.icursor(cursor_pos)

    def update_display(self):
        """Cập nhật nội dung hiển thị dựa trên trạng thái ẩn/hiện."""
        self._is_syncing = True
        if self._is_hidden:
            self.sv.set("*" * len(self._real_text))
        else:
            self.sv.set(self._real_text)
        self._is_syncing = False

    def set_real_text(self, text):
        """Điền mật khẩu ban đầu."""
        self._real_text = text or ""
        self.update_display()

    def get_real_text(self):
        """Lấy mật khẩu thật."""
        return self._real_text

    def toggle_visibility(self):
        """Bật/tắt chế độ ẩn/hiện mật khẩu."""
        self._is_hidden = not self._is_hidden
        self.config(show='*' if self._is_hidden else '')
        self.update_display()