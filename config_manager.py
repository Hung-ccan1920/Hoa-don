import os
import sys
import json
import tempfile
import shutil
from dotenv import load_dotenv, set_key

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

# ==============================================================================
# CONFIGURATION MANAGER CLASS
# ==============================================================================

class ConfigManager:
    """
    A centralized, extensible class for managing all application configurations.
    Operates based on a single schema for consistency.
    """
    CONFIG_SCHEMA = {
        'excel_path': {
            'storage': 'json', 
            'default': '', 
            'required': True, 
            'label': 'Excel Path'
        },
        'API_KEY': {
            'storage': 'env', 
            'default': None, 
            'required': True, 
            'label': 'API Key'
        },
        'USERNAME': {
            'storage': 'env', 
            'default': None, 
            'required': False, 
            'label': 'Username'
        },
        'PASSWORD': {
            'storage': 'env', 
            'default': None, 
            'required': False, 
            'label': 'Password'
        }
    }

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
        set_key(self._dotenv_path, key, value)
        self.secrets[key] = value

    def get(self, key, default=None):
        props = self.CONFIG_SCHEMA.get(key)
        if not props: return default
        
        if props['storage'] == 'json': return self.config.get(key, default)
        elif props['storage'] == 'env': return self.secrets.get(key, default)

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
            messagebox.showinfo("Success", "Configuration saved successfully! Please restart the application.", parent=window)
            window.destroy()
            sys.exit()

        tk.Label(window, text="Please provide the required information:", fg="white", bg="#2e2e2e", font=("Arial", 12)).pack(pady=(10, 5))

        for key in keys_to_ask:
            props = self.CONFIG_SCHEMA[key]
            frame = ttk.Frame(window, style="TFrame")
            frame.pack(pady=5, fill="x", padx=15)
            tk.Label(frame, text=f"{props['label']}:", fg="white", bg="#2e2e2e", font=("Arial", 10), width=15, anchor="w").pack(side="left")

            entry = tk.Entry(frame, font=("Arial", 10), bg="#555555", fg="white", insertbackground="white", relief="solid", borderwidth=1)
            
            if key == 'excel_path':
                choose_button = ttk.Button(frame, text="...", style="Small.TButton", width=3, command=lambda e=entry: self._choose_excel_file(e))
                choose_button.pack(side="right", padx=(5, 0))
            elif key == 'API_KEY':
                guide_button = ttk.Button(frame, text="?", style="Small.TButton", width=3, command=self._open_api_guide)
                guide_button.pack(side="right", padx=(5, 0))

            entry.pack(side="left", expand=True, fill="x")
            entry_widgets[key] = entry
        
        ttk.Button(window, text="Save and Exit", style="Dark.TButton", command=save_values).pack(pady=20)
        window.mainloop()

    def _choose_excel_file(self, entry_widget):
        file_path = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
            
    def _open_api_guide(self):
        video_path = os.path.join(self._root_dir, "Get API key.mp4")
        if os.path.exists(video_path): webbrowser.open(video_path)
        else: messagebox.showwarning("Not Found", "File 'Get API key.mp4' was not found.")

# ==============================================================================
# SETTINGS WINDOW CLASS (for use when the main app is running)
# ==============================================================================

class SettingsWindow(tk.Toplevel):
    """A professional Toplevel window for editing settings."""
    def __init__(self, master, config_manager):
        super().__init__(master)
        self.config_manager = config_manager
        self.title("Settings")
        self.config(bg="#2e2e2e")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self._setup_styles()
        self._create_widgets()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("Dark.TButton", background="#444444", foreground="white", font=("Arial", 10, "bold"), borderwidth=2, padding=10, relief="raised")
        style.map("Dark.TButton", background=[("active", "#555555")], relief=[("pressed", "sunken")])
        style.configure("Small.TButton", font=("Arial", 8, "bold"), padding=(2, 2))
        style.map("Small.TButton", background=[("active", "#555555"), ('!disabled', '#444444')], foreground=[('!disabled', 'white')], relief=[("pressed", "sunken")])

    def _create_widgets(self):
        self.entry_widgets = {}
        tk.Label(self, text="Configuration Settings:", fg="white", bg="#2e2e2e", font=("Arial", 12)).pack(pady=(10, 5))

        for key, props in self.config_manager.CONFIG_SCHEMA.items():
            frame = ttk.Frame(self, style="TFrame")
            frame.pack(pady=5, fill="x", padx=15)
            tk.Label(frame, text=f"{props['label']}:", fg="white", bg="#2e2e2e", font=("Arial", 10), width=15, anchor="w").pack(side="left")

            entry = tk.Entry(frame, font=("Arial", 10), bg="#555555", fg="white", insertbackground="white", relief="solid", borderwidth=1)
            current_value = self.config_manager.get(key)
            if current_value: entry.insert(0, current_value)

            if key == 'excel_path':
                choose_button = ttk.Button(frame, text="...", style="Small.TButton", width=3, command=lambda e=entry: self.config_manager._choose_excel_file(e))
                choose_button.pack(side="right", padx=(5, 0))
            elif key == 'API_KEY':
                guide_button = ttk.Button(frame, text="?", style="Small.TButton", width=3, command=self.config_manager._open_api_guide)
                guide_button.pack(side="right", padx=(5, 0))

            entry.pack(side="left", expand=True, fill="x")
            self.entry_widgets[key] = entry
        
        button_frame = ttk.Frame(self, style="TFrame")
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Save", style="Dark.TButton", command=self._save_values).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", style="Dark.TButton", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _save_values(self):
        for key, entry in self.entry_widgets.items():
            value = entry.get().strip()
            props = self.config_manager.CONFIG_SCHEMA[key]
            if props['required'] and not value:
                messagebox.showwarning("Missing Information", f"The value for '{props['label']}' cannot be empty.", parent=self)
                return
            
            if props['storage'] == 'json':
                self.config_manager.config[key] = value
            else:
                self.config_manager.save_secret(key, value)
        
        self.config_manager.save_config()
        messagebox.showinfo("Success", "Changes saved!", parent=self)
        self.destroy()