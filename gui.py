import utils
import tab1
import tab2
import tkinter as tk
import webbrowser

from tkinter import ttk
from tkinter import messagebox
import os

# Import các lớp cần thiết từ config_manager
from config_manager import SettingsWindow

# --- BƯỚC 2.2: THAY ĐỔI CHỮ KÝ HÀM ---
# Thêm tham số `config` vào hàm
def create_gui(version, config):
    """
    Tạo giao diện chính với 2 tab.
    """
    window = tk.Tk()
    window.title("Chuyên trị hóa đơn")

    # Sử dụng hàm tiện ích để canh giữa màn hình
    utils.center_window(window, 400, 300)

    window.attributes('-topmost', False)
    window.resizable(False, False)
    window.configure(bg="#2e2e2e")

    # --- Thiết lập Style (giữ nguyên) ---
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook", background="#2e2e2e", borderwidth=0)
    style.configure("TNotebook.Tab", background="#333333", foreground="white", font=("Arial", 10, "bold"), padding=(10, 5))
    style.map("TNotebook.Tab", background=[("selected", "#444444")])
    style.configure("TFrame", background="#2e2e2e")
    style.configure("Dark.TButton", background="#444444", foreground="white", font=("Arial", 10, "bold"), borderwidth=2, padding=10, relief="raised")
    style.map("Dark.TButton", background=[("active", "#555555")], relief=[("pressed", "sunken")])
    
    # --- Tạo các widget ---
    notebook = ttk.Notebook(window)
    notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)

    # TAB 1
    tab1TC = ttk.Frame(notebook, style="TFrame")
    notebook.add(tab1TC, text="Tra cứu HĐ")

    # Cấu hình lưới cho tab1
    tab1TC.grid_rowconfigure(0, weight=1)
    tab1TC.grid_rowconfigure(1, weight=1)
    tab1TC.grid_rowconfigure(2, weight=1)
    tab1TC.grid_columnconfigure(0, weight=1)

    label_file = tk.Label(tab1TC, text="Chưa chọn file", bg="#2e2e2e", fg="white", font=("Arial", 12), justify="left", anchor="w")
    label_file.grid(row=0, column=0, pady=10)
    # Truyền `config` vào lệnh của button
    button_tra_cuu = ttk.Button(tab1TC, text="Tra cứu HĐ", style="Dark.TButton", command=lambda: tab1.chon_file(window, label_file, config))
    button_tra_cuu.grid(row=2, column=0, pady=10)

    # TAB 2
    tab2TT = ttk.Frame(notebook, style="TFrame")
    notebook.add(tab2TT, text="Nhập web TT")
    notebook.select(tab2TT)
    # Cấu hình grid cho tab2
    tab2TT.grid_rowconfigure(0, weight=1)
    tab2TT.grid_rowconfigure(1, weight=1)
    tab2TT.grid_rowconfigure(2, weight=1)
    tab2TT.grid_columnconfigure(0, weight=1)
    
    label_info = tk.Label(tab2TT, bg="#2e2e2e", fg="white", font=("Arial", 10), justify="left", anchor="w")
    label_info.grid(row=1, column=0, pady=10)
    button_frame = ttk.Frame(tab2TT, style="TFrame")
    button_frame.grid(row=0, column=0, pady=10)
    # Truyền `config` vào các lệnh của button
    button_import = ttk.Button(button_frame, text="Import HD", style="Dark.TButton", command=lambda: tab2.import_HD(window, label_info, config))
    button_import.pack(side=tk.LEFT, padx=5)
    button_ghi_excel = ttk.Button(button_frame, text="Ghi vào Excel", style="Dark.TButton", command=lambda: tab2.ghi_excel(window, label_info, config))
    button_ghi_excel.pack(side=tk.LEFT, padx=5)
    button_mo_web = ttk.Button(tab2TT, text="Mở web TT", style="Dark.TButton", command=lambda: tab2.web_open(window, label_info, config))
    button_mo_web.grid(row=2, column=0, pady=10)

    menubar = tk.Menu(window)

    # Menu Config
    def open_settings_dialog():
        # Gọi lớp SettingsWindow, truyền vào cửa sổ chính (window) và config
        settings_win = SettingsWindow(master=window, config_manager=config)
        settings_win.wait_window()

    configmenu = tk.Menu(menubar, tearoff=0)
    configmenu.add_command(label="Settings", command=open_settings_dialog) # Đổi tên và chức năng
    menubar.add_cascade(label="Config", menu=configmenu)

    # Menu Help
    def open_user_guide():
        # guide_path = utils.find_file('demo.mp4') 
        guide_path = os.path.join(utils.get_app_path(),'User Guide', 'demo.mp4')
        if os.path.exists(guide_path):
            webbrowser.open(guide_path)
        else:
            messagebox.showwarning("Not Found", "File 'demo.mp4' was not found.")
            
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="User Guide", command=open_user_guide)
    helpmenu.add_separator()
    helpmenu.add_command(label="About", command=lambda: show_about(version))
    menubar.add_cascade(label="Help", menu=helpmenu)
    
    window.config(menu=menubar)

    def on_closing(win):
        # Gọi hàm dọn dẹp tập trung từ ConfigManager
        config.cleanup_temp_dir()
        
        # Tắt web driver
        try:
            if tab1.web_driver and tab1.web_driver.quit:
                tab1.web_driver.quit()
                print("Web driver on tab 1 closed successfully.")
            if tab2.web_driver and tab2.web_driver.quit:
                tab2.web_driver.quit()
                print("Web driver on tab 2 closed successfully.")
        except Exception as e:
            print(f"Error closing web driver: {e}")
        win.destroy()

    window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))

    return window

def show_about(version):
    messagebox.showinfo('About', f"Chuyên trị hóa đơn\n© hung.ledinh\nVersion {version}")