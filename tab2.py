from web_driver_manager import WebDriverManager
import utils

import os
from collections import OrderedDict
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

import time

import xlwings as xw

from pathlib import Path

from collections import defaultdict

import cv2
import numpy as np
import random

import pyautogui

# --- Biến toàn cục ---
HD_info_list = defaultdict()
is_write_excel = False
is_sub_window_open = False
excel_file = None
df = pd.DataFrame()
web_driver = None


def import_HD(window, label, config):
    global is_write_excel, HD_info_list

    file_paths = filedialog.askopenfilenames(
        initialdir="/",
        title="Select PDF or XML Invoices",
        filetypes=(("PDF or XML files", "*.pdf *.xml"),)
    )
    if not file_paths: return

    label.config(text='')
    HD_info_list = []

    utils.update_label(window, label, 'Invoices Imported: ')
    
    order = ['Goi','SHDong', 'NHDong','MST', 'TgTCThue', 'TgTTTBSo', 'KHHDon', 'SHDon', 'NLap', 'MaTC', 'LinkTC', 'path']


    api_keys = config.get('API_KEY')
    for file in file_paths:
        if '.pdf' in file.lower():
            pdf_image_path = config.get_temp_file_path('pdf_import.png')
            HD_info = utils.PDF_file_read(api_keys, file, pdf_image_path)

            xml_path = utils.find_xml_file(file, HD_info)
            HD_info['path'] = xml_path if xml_path else file.replace("/", "\\")
        else: # xml file
            HD_info = utils.XML_file_read(api_keys, file, False)
            HD_info['path'] = file.replace("/", "\\")

        if HD_info:
            ordered_HD_info = OrderedDict((key, HD_info[key]) for key in order if key in HD_info)
            HD_info_list.append(ordered_HD_info)
            utils.update_label(window, label, f'\n{Path(file).name}')
    
    utils.update_label(window, label, '\n#')
    is_write_excel = False
    
def ghi_excel(window, label, config):
    global HD_info_list, is_write_excel
    
    if label.cget("text") == '' or is_write_excel:
        return

    # <<< THAY ĐỔI: Lấy đường dẫn excel từ ConfigManager
    excel_file = config.get('excel_path')

    try:
        if not excel_file or not os.path.isfile(excel_file):
            messagebox.showwarning("File Not Found", "Excel file not found. Please select a new one.")
            new_excel_file = filedialog.askopenfilename(
                title="Select an Excel File",
                filetypes=(("Excel files", "*.xlsx *.xls *.xlsm"), ("All files", "*.*"))
            ).replace("/", "\\")

            if not new_excel_file: return

            # <<< THAY ĐỔI: Lưu đường dẫn mới vào config
            excel_file = new_excel_file
            config.config['excel_path'] = excel_file
            config.save_config()
            messagebox.showinfo("Success", f"New Excel path saved:\n{excel_file}")

        wb = xw.Book(excel_file)
        sheet = wb.sheets.active
    except Exception as e:
        messagebox.showerror("Error", f"Could not open Excel file: {e}")
        return
    
    try:
        last_row = sheet.range("A" + str(sheet.cells.last_cell.row)).end('up').row if sheet.cells.last_cell else 0
    except Exception as e:
        last_row = 0 # Mặc định là 0 nếu sheet trống

    empty_columns = ['B', 'C', 'D', 'E', 'F']

    for HD_info in HD_info_list:
        last_row += 1
        col_idx = 1
        for key, value in HD_info.items():
            while True:
                col_letter = xw.utils.col_name(col_idx)
                if col_letter not in empty_columns:
                    sheet.cells(last_row, col_idx).value = value
                    col_idx += 1
                    break
                col_idx += 1

    is_write_excel = True

    try:
        wb.save()
        utils.update_label(window, label, '\n--> Done!')
    except Exception as e:
        messagebox.showerror('Error', f"Could not save Excel file: {e}")
      

def web_open(window, label, config):

    global excel_file, is_sub_window_open, df

    web_driver_manager = WebDriverManager(window, label)

    if is_sub_window_open: return

    excel_file = config.get('excel_path')
    if not excel_file or not os.path.isfile(excel_file):
        messagebox.showerror("Error", "Excel file path is not set or invalid. Please check Settings.")
        return

    wb = xw.Book(excel_file)
    ws = wb.sheets[0]
    selected_rows = str(ws.range('B1').value).split(',')

    column_names = [chr(i) for i in range(65, 82)]
    data = [ws.range(f"A{row_index}:Q{row_index}").value for row_index in selected_rows]
    df = pd.DataFrame(data, columns=column_names, index=selected_rows)
    df.fillna('', inplace=True)

    if window: utils.update_label(window, label, 'Data loaded from Excel!', False)

    # Bỏ đi chức năng chọn nhiều user
    # user, password = create_user_choose_gui(config) 
    user = config.get('COMPANY_USERNAME')
    password = config.get('COMPANY_PASSWORD')

    if user is None: return

    global web_driver
    if not utils.is_driver_active(web_driver):
        # Nếu trình duyệt chưa hoạt động (chưa mở hoặc đã đóng), khởi tạo lại
        web_driver = web_driver_manager.initialize_web_driver()
        if not web_driver: return # Dừng lại nếu khởi tạo thất bại

    if window:
        window.attributes('-topmost', False)

    login_url = 'http://10.17.69.56/dang-nhap'
    web_driver.get(login_url)

    script = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    web_driver.execute_script(script)

  # Đợi tối đa 30 giây cho đến khi trang tải hoàn toàn
    WebDriverWait(web_driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

    # Kiểm tra user và password để nhập, và kiểm tra đã được đăng nhập chưa
    if user and password and web_driver.current_url == login_url:
        WebDriverWait(web_driver, 10).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'body > app-root > ng-component > div > div > div > div > form > div:nth-child(1) > input'))).send_keys(user)

        web_driver.find_element(By.XPATH, '/html/body/app-root/ng-component/div/div/div/div/form/div[2]/input').send_keys(password)

        for _ in range(3):  # Thử đăng nhập tối đa 3 lần
            if solve_puzzle_captcha(web_driver, config):
                break

    # 1. Chuẩn bị danh sách items theo đúng định dạng yêu cầu
    items = []
    for row in selected_rows:
        items.append({
            'display': f"Dòng {row}: {df.at[row, 'A']}", # Văn bản hiển thị
            'value': str(row)                           # Giá trị trả về (số dòng dạng chuỗi)
        })

    # 2. Định nghĩa hàm callback (hàm sẽ làm gì sau khi người dùng chọn)
    #    Hàm data_insert cần web_driver, ta dùng lambda để truyền nó vào.
    callback = lambda selected_row: data_insert(web_driver, selected_row)

    # 3. Gọi hàm tạo giao diện chung
    utils.create_selection_gui(
        main_window=window,
        title="Ghi thông tin vào Web TT",
        items_to_display=items,
        button_text="Cập nhật",
        on_confirm_callback=callback
    )


def on_closing(main_window, sub_window):
  global is_sub_window_open
  is_sub_window_open = False
  sub_window.destroy()
  main_window.deiconify()

def create_user_choose_gui(config):
    """
    Tạo giao diện chọn user, lấy thông tin từ ConfigManager
    """
    users_str = config.get('USERNAME')
    passwords_str = config.get('PASSWORD')

    if not users_str:
      return None, None

    if len(users_str) == 1:
       return users_str[0], passwords_str[0]
       
    window = tk.Toplevel()  # Sử dụng Toplevel để tạo cửa sổ con
    window.title("Chọn user")

    # Thiết lập dark mode
    window.configure(bg="#2e2e2e")
    style = ttk.Style()
    style.theme_use('clam')
    style.configure(".", background="#2e2e2e", foreground="white")
    style.configure("TRadiobutton", background="#2e2e2e", foreground="white", font=("Arial", 10))
    style.configure("TButton", background="#444444", foreground="white", font=("Arial", 10, "bold"))
    style.map("TButton",
              background=[("active", "#555555"), ("pressed", "#333333")])

    # Biến để lưu giá trị của radio button được chọn
    selected_user = tk.StringVar(value=users_str[0])

    # Tạo frame chứa các radio button và label
    frame_radio = ttk.Frame(window)
    frame_radio.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    # Tạo các cặp radio button và label
    for i, user in enumerate(users_str):
        radio_button = ttk.Radiobutton(frame_radio, variable=selected_user, value=user)
        radio_button.grid(row=i, column=0, sticky="w", padx=5, pady=5)

        label = ttk.Label(frame_radio, text=user)
        label.grid(row=i, column=1, sticky="w")

    done = tk.BooleanVar(value=False)  # Biến để kiểm tra khi nào cửa sổ đóng

        # Tạo nút "Chọn"
    def on_chon_button_click():
        nonlocal username, password
        username =  selected_user.get()
        password = passwords_str[users_str.index(username)]
        done.set(True)
        window.destroy()


    # Tạo nút "Chọn"
    update_button = ttk.Button(window, text="Chọn", style="TButton", command= on_chon_button_click)
    update_button.grid(row=1, column=0, pady=10, padx=5, sticky="ew")


    # Điều chỉnh kích thước cửa sổ ngắn lại theo chiều rộng và tự động tính chiều cao
    height = 75 + len(users_str) * 40
    utils.center_window(window, 200, height)

    # Khởi tạo biến user và password
    username = None
    password = None

    def on_closing():
      nonlocal username, password
      username =  None
      password = None
      window.destroy()

    # Gắn hàm on_closing với sự kiện đóng cửa sổ
    window.protocol("WM_DELETE_WINDOW", on_closing)

    # window.mainloop()
    window.wait_variable(done)  # Chờ biến done thay đổi giá trị

    return username, password  # Trả về user và password sau khi cửa sổ đóng

def data_insert(web_driver, row):
  '''Điền thông tin vào web
    row: index dòng
  '''
  global df

  match web_driver.current_url:
    case 'http://10.17.69.56/thuc-hien-ke-hoach/nhap-cong-viec-co-ky-hop-dong':
      try:
        web_driver.refresh()
        # Đợi tối đa 30 giây cho đến khi trang tải hoàn toàn
        WebDriverWait(web_driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

        # Số hợp đồng
        web_driver.find_element(By.CSS_SELECTOR, 
                                'div.card:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(1) > div:nth-child(2) > input:nth-child(2)').send_keys(
                                    df.at[row,'G'])

        # Nội dung
        web_driver.find_element(By.CSS_SELECTOR, 
                            'div.col-md-4:nth-child(3) > input:nth-child(2)').send_keys(
                              df.at[row,'A'])

        # ngày ký
        web_driver.find_element(By.CSS_SELECTOR, 
                      'body > app-root > app-main-layout > div > app-work-with-contract > div.card.mb-3 > div.card-body > form > div > div:nth-child(5) > p-calendar > span > input').send_keys(
                        utils.to_time_from_df(df.at[row,'H']))

        # Ngày làm việc
        web_element = web_driver.find_element(By.CSS_SELECTOR, 'body > app-root > app-main-layout > div > app-work-with-contract > div.card.mb-3 > div.card-body > form > div > div:nth-child(7) > select')
        select = Select(web_element)
        select.select_by_index(1)

        # Nhà cung cấp
        # bấm tìm kiếm
        web_driver.find_element(By.CSS_SELECTOR,
                                'body > app-root > app-main-layout > div > app-work-with-contract > div.card.mb-3 > div.card-body > form > div > div:nth-child(4) > button').click()

        # Đợi trường MST có và nhập vào
        WebDriverWait(web_driver, 3).until(EC.visibility_of_element_located((By.XPATH, 
                                                                              "/html/body/p-dynamicdialog/div/div/div[2]/app-search-supplier/div[1]/div/form/div/div[1]/input"))).send_keys(
                                                                                  df.at[row,'I'])

        # bấm tìm kiếm
        web_driver.find_element(By.XPATH, 
                                '/html/body/p-dynamicdialog/div/div/div[2]/app-search-supplier/div[1]/div/form/div/div[3]/button').click()
        
        # Tìm nút chọn
        web_element = web_driver.find_element(By.XPATH, '/html/body/p-dynamicdialog/div/div/div[2]/app-search-supplier/div[2]/div/div/button')
        
        # Bấm tab để tới radio bution đầu tiên
        web_element.send_keys(Keys.TAB)
        time.sleep(0.5)  # Chờ 1 giây

        # Lấy active element là radio bution
        active_element = web_driver.switch_to.active_element
        web_driver.execute_script("arguments[0].click();", active_element)

        # bấm nút chọn
        web_element.click()
      except Exception as e:
        messagebox.showerror('Lỗi',e)
    case 'http://10.17.69.56/ke-khai-ho-so/ban-than':
      try:
        web_driver.refresh()

        # Đợi tối đa 30 giây cho đến khi trang tải hoàn toàn
        WebDriverWait(web_driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

        #Loại thanh toán
        

                
        # Bấm nút MST
        web_driver.find_element(By.XPATH,
                                '/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[1]/div[2]/app-declare-profile-form/form/div/div[8]/button').click()
        # Đợi trường MST có và nhập vào  
        WebDriverWait(web_driver, 3).until(EC.visibility_of_element_located((By.XPATH, 
                                                                              "/html/body/p-dynamicdialog/div/div/div[2]/app-search-supplier/div[1]/div/form/div/div[1]/input"))).send_keys(
                                                                                  df.at[row,'I'])

        # bấm tìm kiếm
        web_driver.find_element(By.XPATH, 
                                '/html/body/p-dynamicdialog/div/div/div[2]/app-search-supplier/div[1]/div/form/div/div[3]/button').click()
        
        # Tìm nút chọn
        web_element = web_driver.find_element(By.XPATH, '/html/body/p-dynamicdialog/div/div/div[2]/app-search-supplier/div[2]/div/div/button')
        
        # Bấm tab để tới radio bution đầu tiên
        web_element.send_keys(Keys.TAB)
        time.sleep(0.5)  # Chờ 1 giây

        # Lấy active element là radio bution
        active_element = web_driver.switch_to.active_element
        web_driver.execute_script("arguments[0].click();", active_element)

        # bấm nút chọn
        web_element.click()

        # Nội dung thanh toán 
        web_driver.find_element(By.XPATH, 
                                '/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[1]/div[2]/app-declare-profile-form/form/div/div[12]/div/textarea').send_keys(
                                    df.at[row,'F'])
        
        # Kèm theo
        web_driver.find_element(By.XPATH, 
                                '/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[1]/div[2]/app-declare-profile-form/form/div/div[13]/textarea').send_keys(
                                    'Giấy đề nghị thanh toán'
                                    '\nHóa đơn GTGT')

        # kiểm tra có mã tra cứu không để nhập hóa đơn
        if df.at[row,'O']:
          # bấm có hóa đơn
          web_driver.find_element(By.XPATH, 
                                '/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[1]/div[2]/app-declare-profile-form/form/div/div[15]/p-inputswitch/div/span').click()
          # Đợi trường link có và nhập vào  
          WebDriverWait(web_driver, 3).until(EC.visibility_of_element_located((By.XPATH, 
                                                                                "/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[1]/div[2]/app-declare-profile-form/form/div/div[16]/p-tabview/div/div//input[@formcontrolname='link']"))).send_keys(
                                                                                    df.at[row,'P'])
          # mã TC 
          web_driver.find_element(By.XPATH, 
                          "/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[1]/div[2]/app-declare-profile-form/form/div/div[16]/p-tabview/div/div//input[@formcontrolname='secretKey']").send_keys(
                              df.at[row,'O'])
          
          try:
            # Kiểm tra đường dẫn file xml có không, k thì thử tìm lại
            xml_path = df.at[row, 'Q']
            if '.xml' not in xml_path:
              xml_path = utils.find_xml_file(xml_path)

            if xml_path:            
              # Gán đường dẫn file xml để tải thủ công (nhập thẳng vào thẻ input ẩn)
              web_driver.find_element(By.XPATH, '//*[@id="attch-annex"]').send_keys(xml_path)
            else:
                # Nếu không có thì bấm download tự động
                web_driver.find_element(By.XPATH, 
                                        '//*[@id="ui-tabpanel-0"]/div/div/div[4]/div/button[1]').click()
                
                # lớp phủ biến mất đi khi tải xong
                WebDriverWait(web_driver, 10).until(EC.invisibility_of_element_located((By.XPATH, '/html/body/app-root/ngx-spinner/div/div[2]')))

                # Đợi thông báo lỗi không tải được và bấm tắt thông báo, nếu tải thành công thì lệnh này sẽ lỗi
                WebDriverWait(web_driver, 3).until(EC.visibility_of_element_located((By.XPATH, 
                                                                                "/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[2]/div/app-payment-file-table/p-confirmdialog/div/div/div[1]/div/a"))).click()
          except: # nếu lỗi thì đã tải thành công
            pass

        # Bấm nút ERP
        WebDriverWait(web_driver, 3).until(EC.visibility_of_element_located((By.XPATH, 
                                                                      "/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[1]/div[2]/app-declare-profile-form/form/div/div[6]/div/div[2]/button"))).click()

        # Thêm ERP
        WebDriverWait(web_driver, 3).until(EC.visibility_of_element_located((By.XPATH, 
                                                                              "/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[1]/div[2]/app-declare-profile-form/form/div/div[6]/div[2]/div/div/div[2]/div[1]/input"))).send_keys(
                                                                                  str(df.at[row,'D']).replace('.0',''))
        # bấm nút chọn mã
        WebDriverWait(web_driver, 3).until(EC.visibility_of_element_located((By.XPATH, 
                                                                      "/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[1]/div[2]/app-declare-profile-form/form/div/div[6]/div[2]/div/div/div[2]/div[2]/button"))).click()
      except Exception as e:
        messagebox.showerror('Lỗi',e)

def find_drag_offset(background_image_path):
    pixel_count_threshold = 27  # Số pixel màu trắng để đếm
    color_threshold = 210       # Ngưỡng màu để tạo ảnh đen/trắng
    scale = 1/0.93808           # Điều chỉnh distance theo tỉ lệ
    offset = -5                # Điều chỉnh offset

    # output_dir = "debug_images"
    # os.makedirs(output_dir, exist_ok=True)

    try:
        # --- BƯỚC 1: Đọc ảnh và chuyển sang ảnh xám ---
        background_img = cv2.imread(background_image_path)
        if background_img is None:
            print("Error: Could not read the background image.")
            return None
            
        gray_img = cv2.cvtColor(background_img, cv2.COLOR_BGR2GRAY)
        # cv2.imwrite(os.path.join(output_dir, "step1_grayscale.png"), gray_img)
        # print("Saved: step1_grayscale.png")

        # --- BƯỚC 2: Áp dụng Phân ngưỡng Nhị phân để tạo ảnh đen/trắng ---
        _, binary_img = cv2.threshold(gray_img, color_threshold, 255, cv2.THRESH_BINARY)
        # cv2.imwrite(os.path.join(output_dir, "step2_binary.png"), binary_img)
        # print("Saved: step2_binary.png")
        
        # --- BƯỚC 3: Quét ảnh từ trái sang phải để tìm cạnh ---
        height, width = binary_img.shape
        
        # Bỏ qua vị trí của miếng ghép ban đầu
        start_x = 66 
        
        print(f"Scanning image from x={start_x} to x={width}...")
        
        # Lặp qua từng cột pixel theo chiều rộng
        for x in range(start_x, width):
            # Lấy ra một dải ảnh dọc tại vị trí x
            vertical_strip = binary_img[:, x]
            
            # Đếm số pixel trắng (giá trị > 0) trong dải ảnh đó
            white_pixel_count = np.count_nonzero(vertical_strip)
            
            # In ra để theo dõi 
            # if white_pixel_count > 10: print(f"Column x={x}, White Pixels={white_pixel_count}")

            # Nếu số pixel trắng vượt ngưỡng, chúng ta đã tìm thấy cạnh
            if white_pixel_count >= pixel_count_threshold:
                print(f"--> Edge found at x = {x} with {white_pixel_count} white pixels (threshold was {pixel_count_threshold}).")
                
                # Vẽ một đường thẳng đỏ lên ảnh gốc để đánh dấu vị trí tìm được
                cv2.line(background_img, (x, 0), (x, height), (0, 0, 255), 2)
                # cv2.imwrite(os.path.join(output_dir, "step3_result.png"), background_img)
                # print("Saved: step3_result.png with the detected edge.")

                return x * scale + offset
        
        print("Could not find any vertical edge matching the threshold.")
        return None

    except Exception as e:
        print(f"An error occurred during image processing: {e}")
        return None

def solve_puzzle_captcha(driver, config):
    """Hàm tổng hợp các bước để giải captcha.""" 
    try:
        # --- 1. Lấy hình ảnh ---
        background_selector = "body > app-root > ng-component > div > div > div > div > form > app-ngx-slider-recaptcha > div > canvas.canvas" 
        slider_handle_selector = "body > app-root > ng-component > div > div > div > div > form > app-ngx-slider-recaptcha > div > div > div > div" 
        slider_container_selector = "body > app-root > ng-component > div > div > div > div > form > app-ngx-slider-recaptcha > div > div"
       
        print("Capturing captcha images...")
        background_path = config.get_temp_file_path('bg.png')
        driver.find_element(By.CSS_SELECTOR, background_selector).screenshot(background_path)

        # --- 2. Tính toán khoảng cách ---
        distance = find_drag_offset(background_path)
        if distance is None:
            print("Could not calculate drag distance.")
            return False
        
        print(f"Calculated drag distance: {distance}px")

        slider_handle_element = driver.find_element(By.CSS_SELECTOR, slider_handle_selector)
        slider_container_element = driver.find_element(By.CSS_SELECTOR, slider_container_selector)

        # 1. Lấy vị trí và kích thước của núm trượt trên màn hình
        location = slider_handle_element.location
        size = slider_handle_element.size
        
        # Tính toán điểm bắt đầu (ở giữa núm trượt)
        start_x = location['x'] + size['width']/2
        start_y = location['y'] + driver.find_element(By.CSS_SELECTOR, background_selector).size['height'] # Cộng thêm chiều cao của ảnh

        drag_with_real_mouse(start_x, start_y, distance)  

        time.sleep(2)  # Chờ 2 giây để tránh kiểm tra quá sớm
        
        if 'success' in slider_container_element.get_attribute('class'):
            print("✅ Slider captcha solved successfully!")
            return True
        else:
            print("❌ Slider captcha failed (Incorrect position).")
            return False
    except TimeoutException:
        print("❌ Slider captcha failed (Verification timed out).")
        return False
    except Exception as e:
        print(f"❌ An error occurred during captcha solving: {e}")
        return False

def drag_with_real_mouse(start_x, start_y, distance):
    """
    Điều khiển con trỏ chuột thật của hệ thống để thực hiện kéo thả.

    Args:
        driver: Đối tượng WebDriver.
        slider_element: Element của núm trượt.
        distance (int): Khoảng cách cần kéo.
    """
    try:
        # 2. Di chuyển con trỏ chuột thật đến điểm bắt đầu
        pyautogui.moveTo(start_x, start_y, duration=0.2) # Di chuyển trong 0.2 giây

        # 3. Nhấn và giữ chuột trái
        pyautogui.mouseDown()
        
        # 4. Di chuyển chuột đến một khoảng cách `distance`
        # --- Tạo quỹ đạo di chuyển không theo đường thẳng ---
        current_x, current_y = pyautogui.position()
        target_x = current_x + distance
        
        # Chia quãng đường thành nhiều đoạn nhỏ
        num_steps = random.randint(15, 25)
        
        for i in range(1, num_steps + 1):
            # Tính toán vị trí tiếp theo trên một đường cong (ease-in-out)
            t = i / num_steps
            eased_t = t * t * (3 - 2 * t) # Công thức ease-in-out
            
            x = current_x + (eased_t * distance)
            
            # Thêm một chút "nhiễu" theo trục y để trông giống người hơn
            y = current_y + random.uniform(-3, 3) 
            
            # Di chuyển đến điểm tiếp theo với thời gian ngẫu nhiên
            pyautogui.moveTo(x, y, duration=random.uniform(0.01, 0.03))

        # Đảm bảo con trỏ đến đúng vị trí cuối cùng
        pyautogui.moveTo(target_x, current_y, duration=0.1)
        # 5. Thả chuột trái ra
        pyautogui.mouseUp()
        
        return True
    except Exception as e:
        print(f"An error occurred during real mouse drag: {e}")
        return False