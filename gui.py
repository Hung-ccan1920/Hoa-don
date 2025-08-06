import utils
import tab1
import tab2

import tkinter as tk
import os
import webbrowser # Thư viện mới để mở file và video

from tkinter import ttk
from tkinter import messagebox


def open_config_file():
    """Mở file config.txt bằng trình soạn thảo văn bản mặc định của hệ thống."""
    config_path = utils.find_file('config.txt')
    if config_path:
        try:
            # Sử dụng webbrowser để mở file, cách này tương thích đa nền tảng
            webbrowser.open(config_path)
            print(f"Đang mở file: {config_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi mở file config: {e}")
    else:
        # Nếu file không tồn tại, thông báo cho người dùng
        messagebox.showwarning("Không tìm thấy", f"Không tìm thấy file '{config_path}' trong thư mục của ứng dụng.")

def open_user_guide():
    """Mở video hướng dẫn v2 demo.mp4 bằng trình phát video mặc định."""
    guide_path = utils.find_file('demo.mp4')
    if guide_path:
        try:
            webbrowser.open(guide_path)
            print(f"Đang mở video hướng dẫn: {guide_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi mở video: {e}")
    else:
        # Nếu file video không tồn tại, thông báo cho người dùng
        messagebox.showwarning("Không tìm thấy", f"Không tìm thấy file video '{guide_path}' trong thư mục của ứng dụng.")


def create_gui(version):
    """
    Tạo giao diện chính với 2 tab: "Tra cứu HĐ" và "Nhập web TT".
    """

    # Tạo cửa sổ chính
    window = tk.Tk()
    window.title("Chuyên trị hóa đơn")

    # Định vị cửa sổ ở giữa màn hình
    window.geometry(utils.window_center_position(400, 300))

    # Đặt cửa sổ luôn ở trên cùng
    window.attributes('-topmost', False)

    window.resizable(False, False)  # Không cho phép thay đổi kích thước

    window.configure(bg="#2e2e2e")  # Màu nền xám đen

    # Thiết lập Style cho Dark Mode
    style = ttk.Style()
    style.theme_use("clam")

    # Cấu hình style cho TNotebook
    style.configure("TNotebook", background="#2e2e2e", borderwidth=0)
    style.configure("TNotebook.Tab",
                    background="#333333", 
                    foreground="white", 
                    font=("Arial", 10, "bold"),
                    padding=(10, 5))
    style.map("TNotebook.Tab", background=[("selected", "#444444")])

    # Cấu hình style cho TFrame và Button
    style.configure("TFrame", background="#2e2e2e")

    style.configure("Dark.TButton",
                    background="#444444",  # Màu nền nút
                    foreground="white",    # Màu chữ
                    font=("Arial", 10, "bold"),
                    borderwidth=2,
                    padding=10,
                    relief="raised")

    style.map("Dark.TButton",
            background=[("active", "#555555")],  # Hover
            relief=[("pressed", "sunken")])      # Hiệu ứng nhấn
    
    # Hiệu ứng hover và nhấn
    style.map("Custom.TButton",
            background=[("active", "#555555"),  # Hover
                        ("pressed", "#333333")],  # Nhấn
            relief=[("pressed", "sunken")])     # Hiệu ứng nhấn chìm

    # Tạo Notebook (tab control)
    notebook = ttk.Notebook(window)
    notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Định nghĩa cấu trúc lưới (grid structure) chính
    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)

    # TAB 1: Tra cứu HĐ
    tab1TC = ttk.Frame(notebook)
    notebook.add(tab1TC, text="Tra cứu HĐ")

    # Cấu hình lưới cho tab1
    tab1TC.grid_rowconfigure(0, weight=1)
    tab1TC.grid_rowconfigure(1, weight=1)
    tab1TC.grid_rowconfigure(2, weight=1)
    tab1TC.grid_columnconfigure(0, weight=1)

    # Label hiển thị tên file
    label_file = tk.Label(tab1TC, text="Chưa chọn file", bg="#2e2e2e", fg="white", font=("Arial", 12), justify="left", anchor="w")
    label_file.grid(row=0, column=0, pady=10)

    # Button "Tra cứu HĐ"
    button_tra_cuu = ttk.Button(tab1TC, text="Tra cứu HĐ", style="Dark.TButton", command=lambda: tab1.chon_file(window,label_file))
    button_tra_cuu.grid(row=2, column=0, pady=10)

    # TAB 2: Nhập web TT
    tab2TT = ttk.Frame(notebook)
    notebook.add(tab2TT, text="Nhập web TT")
    notebook.select(tab2TT)  # Chọn tab2TT khi mới mở

    # Cấu hình lưới cho tab2
    tab2TT.grid_rowconfigure(0, weight=1)
    tab2TT.grid_rowconfigure(1, weight=1)
    tab2TT.grid_rowconfigure(2, weight=1)
    tab2TT.grid_columnconfigure(0, weight=1)

        
    # Label thông tin
    label_info = tk.Label(tab2TT, bg="#2e2e2e", fg="white", font=("Arial", 10), justify="left", anchor="w")
    label_info.grid(row=1, column=0, pady=10)

    # Frame chứa các nút bấm
    button_frame = tk.Frame(tab2TT, bg="#2e2e2e")
    button_frame.grid(row=0, column=0, pady=10)

    # Button "Import"
    button_import = ttk.Button(button_frame, text="Import HD", style="Dark.TButton", command= lambda: tab2.import_HD(window,label_info))
    button_import.pack(side=tk.LEFT, padx=5)

    # Button "Ghi vào excel"
    button_ghi_excel = ttk.Button(button_frame, text="Ghi vào Excel", style="Dark.TButton", command= lambda: tab2.ghi_excel(window,label_info))
    button_ghi_excel.pack(side=tk.LEFT, padx=5)

    # Button "Mở web TT"
    button_mo_web = ttk.Button(tab2TT, text="Mở web TT", style="Dark.TButton", command=lambda: tab2.web_open(window,label_info))
    button_mo_web.grid(row=2, column=0, pady=10)

    # --- BẮT ĐẦU PHẦN CHỈNH SỬA MENU ---
    
    # Tạo menu bar chính
    menubar = tk.Menu(window)

    # 1. Tạo menu "Config" (mới)
    configmenu = tk.Menu(menubar, tearoff=0)
    configmenu.add_command(label="Open Config File", command=open_config_file)
    menubar.add_cascade(label="Config", menu=configmenu)

    # 2. Chỉnh sửa menu "Help"
    helpmenu = tk.Menu(menubar, tearoff=0)
    # Thêm mục "Hướng dẫn sử dụng" vào TRƯỚC mục "About"
    helpmenu.add_command(label="User Guide", command=open_user_guide)
    helpmenu.add_separator() # Thêm dòng kẻ ngang để phân cách cho đẹp
    helpmenu.add_command(label="About", command=lambda:show_about(version))
    menubar.add_cascade(label="Help", menu=helpmenu)
    
    window.config(menu=menubar)

    # --- KẾT THÚC PHẦN CHỈNH SỬA MENU ---

    # Gắn hàm on_closing với sự kiện đóng cửa sổ
    window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))

    # Chạy ứng dụng
    return window

def show_about(version):
    messagebox.showinfo('About', f"Chuyên trị hóa đơn\n© hung.ledinh\nVersion {version}")

def on_closing(window):
    """
    Hàm xử lý sự kiện đóng cửa sổ: dọn dẹp các tệp tạm và đóng ứng dụng.
    """
    # Danh sách các tệp có thể cần xóa
    files_to_delete = ['pdf.png', 'captcha.png', 'screenshot.png']
    
    print("Đóng ứng dụng, bắt đầu dọn dẹp các tệp tạm...")

    # Duyệt qua danh sách và xóa từng tệp một cách an toàn
    for file_path in files_to_delete:
        try:
            # Chỉ xóa nếu tệp tồn tại
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"   -> Đã xóa: {file_path}")
        except OSError as e:
            # Báo lỗi nếu không xóa được (ví dụ: do file đang được sử dụng)
            print(f"Lỗi không thể xóa file {file_path}: {e}")

    # Chỉ gọi destroy MỘT LẦN ở cuối cùng, sau khi đã dọn dẹp xong
    window.destroy()