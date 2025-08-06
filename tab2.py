import os
import utils
import password_manager

from collections import OrderedDict
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

import time

import xlwings as xw

from pathlib import Path

from collections import defaultdict

import pyperclip

HD_info_list = defaultdict()

is_write_excel = False
is_sub_window_open = False
is_web_opened = False
df = pd.DataFrame()

excel_file = None


def import_HD(window, label):
  global is_write_excel, HD_info_list

  file_paths = filedialog.askopenfilenames(
      initialdir="/",
      title="Chọn HÓa đơn PDF",
      filetypes=( ("PDF or XML files", "*.pdf *.xml"), )
  )
  if len(file_paths)>0:
    label.config(text='')  # Xóa nội dung label
    HD_info_list = [] # Xóa nội dung

    utils.update_label(window, label,'Hóa đơn đã được import: ')
    
    # HD_info = utils.PDF_file_read(ten_file)
    # Thứ tự các nhãn mong muốn
    order = ['Goi','SHDong', 'NHDong','MST', 'TgTCThue', 'TgTTTBSo', 'KHHDon', 'SHDon', 'NLap', 'MaTC', 'LinkTC', 'path']

    for file in file_paths:
      if '.pdf' in file:
        HD_info = utils.PDF_file_read(file)
        # Tìm file xml, nếu không có thì trả về đường dẫn file pdf, để tìm lại sau
        if path := utils.find_xml_file(file, HD_info):
          HD_info['path'] = path
        else:
          HD_info['path'] = file.replace("/", "\\")
      else:
        HD_info = utils.XML_file_read(file, True)
        HD_info['path'] = file.replace("/", "\\")

      if len(HD_info) > 0: 
         # sắp xếp theo thứ tự order
        ordered_HD_info = OrderedDict((key, HD_info[key]) for key in order if key in HD_info)

        HD_info_list.append(ordered_HD_info)

        utils.update_label(window, label,f'\n{Path(file).name}')
    
    utils.update_label(window, label,'\n#')
    
    # reset lại biến
    is_write_excel = False
    
def ghi_excel(window, label):
    """
    Ghi nội dung vào file Excel.

    """

    global HD_info_list, is_write_excel, excel_file
    if not excel_file:
      excel_file = utils.config_file_value ('Excel')[0]

    if  label.cget("text") == '' or is_write_excel:
        return

    try:
        #kiêm tra file excel tồn tại không
        # Check if the file exists
        if not os.path.isfile(excel_file):
          print(f"File Exxcel not found. Please select an Excel file.")
        
          # Create the main tkinter window and hide it
          root = tk.Tk()
          root.withdraw()

          # Show an "Open" dialog box and get the path of the selected file
          excel_file = filedialog.askopenfilename(
              title="Select an Excel File",
              filetypes=(
                  ("Excel files", "*.xlsx *.xls *xlsm"),
                  ("All files", "*.*"))).replace("/", "\\")
          if not excel_file:
             return

          utils.write_config_file('Excel', excel_file)

        # Mở workbook bằng xlwings. Không cần kiểm tra file có mở hay không
        wb = xw.Book(excel_file)  # Mở workbook. Nếu file không tồn tại sẽ báo lỗi
        sheet = wb.sheets.active #lấy sheet hiện tại
    except FileNotFoundError:
        messagebox.showerror('Lỗi', f"Không tìm thấy file Excel: {excel_file}")
        return
    except Exception as e: # Bắt các lỗi khác nếu có
        messagebox.showerror("Lỗi", f"Lỗi khi mở file Excel: {e}")
        return
    
    try:
      last_row = sheet.range("A" + str(sheet.cells.last_cell.row)).end('up').row if sheet.cells.last_cell else 0
    except Exception as e:
      messagebox.showerror("Lỗi", f"Lỗi khi xác định dòng cuối cùng: {e}")
      return

    empty_columns = ['B', 'C', 'D', 'E', 'F']

    for HD_info in HD_info_list:
        last_row += 1
        col_idx = 1
        for key, value in HD_info.items():
            while True:
                col_letter = xw.utils.col_name(col_idx)
                if col_letter not in empty_columns:
                  try:
                    sheet.cells(last_row, col_idx).value = value
                  except Exception as e:
                    messagebox.showerror("Lỗi", f"Lỗi khi ghi dữ liệu vào ô: {e}")
                    return
                  col_idx += 1
                  break
                col_idx += 1

    is_write_excel = True

    try:
        wb.save() # Lưu file
        utils.update_label(window, label,'\n--> Xong!')
    except Exception as e:
        messagebox.showerror('Lỗi', f"Lỗi khi lưu file Excel: {e}")
        return
      

def web_open(window, label):

  global excel_file, is_sub_window_open, df

  if not excel_file:
    excel_file = utils.config_file_value ('Excel')[0]
  
  # Kiểm tra cửa sổ đã được mở chưa
  if is_sub_window_open:
    return

  wb = xw.Book(excel_file)
  ws = wb.sheets[0]  # Lấy sheet đầu tiên
  # selected_rows = ws.range('R1').value
  selected_rows = str(ws.range('B1').value).split(',')

  # Lấy tên các cột (từ A đến Q)
  column_names = [chr(i) for i in range(65, 82)]  # 65 là mã ASCII của 'A', 81 là mã ASCII của 'Q'

  # Lưu thông tin từ cột A đến cột Q của các dòng được chọn vào DataFrame
  data = []
  for row_index in selected_rows:
      row_data = ws.range(f"A{row_index}:Q{row_index}").value  # Lấy dữ liệu từ cột A đến Q
      data.append(row_data)

  # Tạo DataFrame với column_names làm nhãn và selected_row làm index
  df = pd.DataFrame(data, columns=column_names, index=selected_rows)
  
  # Gán giá trị cho ô rỗng
  df.fillna('', inplace=True)

  utils.update_label(window, label,'Đã lấy dữ liệu từ Excel!',False)

  # Chọn password trước khi mở web
  user, password = create_user_choose_gui()

  global is_web_opened
  try:
      if not(is_web_opened) or web_driver.title: #Kiểm tra web đã được mở chưa
          web_driver = utils.initialize_web_driver(window, label)
          is_web_opened = True
  except:
      # khi trang web bị người dùng tắt, web_driver.title sẽ bị lỗi, khởi tạo lại trang web
      web_driver = utils.initialize_web_driver(window, label)
      is_web_opened = True

  # Bỏ chế độ ontop khi mở trang web
  window.attributes('-topmost', False)

  # Mở trang web
  web_driver.get('http://10.17.69.56/dang-nhap')

  # Kiểm tra user và password để nhập vào
  if user and password:
    WebDriverWait(web_driver, 10).until(EC.presence_of_element_located(
      (By.CSS_SELECTOR, 'body > app-root > ng-component > div > div > div > div > form > div:nth-child(1) > input'))).send_keys(user)

    web_driver.find_element(By.CSS_SELECTOR, 'body > app-root > ng-component > div > div > div > div > form > div._c5f7bb96._aeaddae9._f2cdb69f._1b1d59f6._119fcfce._b75720eb._95467085.ng-tns-c55-4 > input').send_keys(password)

    web_driver.find_element(By.CSS_SELECTOR, 'body > app-root > ng-component > div > div > div > div > form > div.row.justify-content-center.ng-tns-c55-4 > button').click()

  # Mở màn hình chọn dòng để update thong tin vao web
  create_write_web_gui(window,web_driver, selected_rows)
  is_sub_window_open = True

  window.mainloop()


def create_write_web_gui(main_window, web_driver, rows):
    """
    Tạo giao diện dark mode với các cặp radio button và label, 
    và nút "Cập nhật" ở dưới cùng.

    Args:
        rows (list): Danh sách các số dòng.
    """
    main_window.withdraw()

    sub_window = tk.Toplevel()  # Sử dụng Toplevel để tạo cửa sổ con
    sub_window.title("Ghi thông tin vào Web TT")

    # Thiết lập dark mode
    sub_window.configure(bg="#2e2e2e")
    style = ttk.Style()
    style.theme_use('clam')
    style.configure(".", background="#2e2e2e", foreground="white")
    style.configure("TRadiobutton", background="#2e2e2e", foreground="white", font=("Arial", 10))
    style.configure("TButton", background="#444444", foreground="white", font=("Arial", 10, "bold"))
    style.map("TButton",
              background=[("active", "#555555"), ("pressed", "#333333")])

    # Biến để lưu giá trị của radio button được chọn
    selected_row = tk.IntVar(value=rows[0])

    # Tạo frame chứa các radio button và label
    frame_radio = ttk.Frame(sub_window)
    frame_radio.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    # Tạo các cặp radio button và label
    for i, row in enumerate(rows):
        radio_button = ttk.Radiobutton(frame_radio, text=f"Dòng {row}", variable=selected_row, value=row)
        radio_button.grid(row=i, column=0, sticky="w", padx=5, pady=5)

        label = ttk.Label(frame_radio, text=df.at[row, 'A'])
        label.grid(row=i, column=1, sticky="w")

    # Tạo nút "Cập nhật"
    update_button = ttk.Button(sub_window, text="Cập nhật", style="TButton", command= lambda: data_insert(web_driver, str(selected_row.get())))
    update_button.grid(row=1, column=0, pady=10, padx=5, sticky="ew")


    # Điều chỉnh kích thước cửa sổ ngắn lại theo chiều rộng và tự động tính chiều cao
    height = 75 + len(rows) * 40
    sub_window.geometry(utils.window_center_position(300,height))

    # Gắn hàm on_closing với sự kiện đóng cửa sổ
    sub_window.protocol("WM_DELETE_WINDOW", lambda: on_closing(main_window, sub_window))

    sub_window.mainloop()

def on_closing(main_window, sub_window):
  global is_sub_window_open, df
  is_sub_window_open = False
  sub_window.destroy()
  main_window.deiconify()

def create_user_choose_gui():
    """
    Tạo giao diện dark mode với các cặp radio button và label, 
    và nút "chọn user" ở dưới cùng.

    """
    #Lấy thông tin user từ file config
    users = utils.config_file_value('username')
    if not users:
      return None, None

    if len(users) == 1:
       return users[0], password_manager.decrypt_password(utils.config_file_value('password')[0])
       
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
    selected_user = tk.StringVar(value=users[0])

    # Tạo frame chứa các radio button và label
    frame_radio = ttk.Frame(window)
    frame_radio.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    # Tạo các cặp radio button và label
    for i, user in enumerate(users):
        radio_button = ttk.Radiobutton(frame_radio, variable=selected_user, value=user)
        radio_button.grid(row=i, column=0, sticky="w", padx=5, pady=5)

        label = ttk.Label(frame_radio, text=user)
        label.grid(row=i, column=1, sticky="w")

    done = tk.BooleanVar(value=False)  # Biến để kiểm tra khi nào cửa sổ đóng

        # Tạo nút "Chọn"
    def on_chon_button_click():
        nonlocal username, password
        username =  selected_user.get()
        password = utils.config_file_value('password')[users.index(user)]
        done.set(True)
        window.destroy()


    # Tạo nút "Chọn"
    update_button = ttk.Button(window, text="Chọn", style="TButton", command= on_chon_button_click)
    update_button.grid(row=1, column=0, pady=10, padx=5, sticky="ew")


    # Điều chỉnh kích thước cửa sổ ngắn lại theo chiều rộng và tự động tính chiều cao
    height = 75 + len(users) * 40
    window.geometry(utils.window_center_position(200,height))

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

    return username, password_manager.decrypt_password(password)  # Trả về user và password sau khi cửa sổ đóng

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
          
          #bấm nút Download tự đông:
          # edge_driver.find_element(By.XPATH, 
          #                         '//*[@id="ui-tabpanel-0"]/div/div/div[4]/div/button[1]').click()
          
          # lớp phủ biến mất đi khi tải xong
          # WebDriverWait(edge_driver, 10).until(EC.invisibility_of_element_located((By.XPATH, '/html/body/app-root/ngx-spinner/div/div[2]')))
          
          try:
            # Đợi thông báo lỗi không tải được và bấm tắt thông báo
            # WebDriverWait(edge_driver, 5).until(EC.visibility_of_element_located((By.XPATH, 
            #                                                                     "/html/body/app-root/app-main-layout/div/app-pre-file-statement/div[2]/div/app-payment-file-table/p-confirmdialog/div/div/div[1]/div/a"))).click()
            # Kiểm tra đường dẫn file xml có không, k thì thử tìm lại
            xml_path = df.at[row, 'Q']
            if '.xml' not in xml_path:
              xml_path = utils.find_xml_file(xml_path)

            if xml_path:
              # #bấm nút upload thủ công: 
              # edge_driver.find_element(By.XPATH, 
              #                       '//*[@id="ui-tabpanel-0"]/div/div/div[4]/div/button[2]').click()
              # # Chờ hộp thoại xuất hiện
              # time.sleep(4)
              # value_to_copy = xml_path
              # pyperclip.copy(value_to_copy)
              # pywinauto.keyboard.send_keys("^v")  # Dán (Ctrl+V)
              # pywinauto.keyboard.send_keys("{ENTER}")

              #time.sleep(2)
              
              # Gán đường dẫn file xml để tải thủ công (nhập thẳng vào thẻ input ẩn)
              web_driver.find_element(By.XPATH, '//*[@id="attch-annex"]').send_keys(xml_path)

          except: # nếu lỗi thì đã tải thành công
            None

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



  

