import utils
from ai_manager import AIManager
from web_driver_manager import WebDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from tkinter import filedialog, messagebox

from PIL import ImageGrab
import win32api
import win32print
import pywinauto
from pathlib import Path

from collections import defaultdict
# Biến toàn cục 
web_driver = None # Giữ instance của trình duyệt

def chon_file(window, label, config):
    """
    Hàm chính xử lý logic tra cứu hóa đơn.
    """
    file_paths = filedialog.askopenfilenames(
        initialdir="/",
        title="Select XML or PDF Invoices",
        filetypes=(("XML and PDF files", "*.xml *.pdf"), )
    )

    if not file_paths: # Nếu người dùng hủy
        return

    label.config(text='')

    invoices_info_list = defaultdict(list)
    
    api_keys = config.get('API_KEY')
    for file in file_paths:
        if '.xml' in file:
            invoices_info = utils.XML_file_read(api_keys, file, False)
        else:
            pdf_image_path = config.get_temp_file_path('pdf.png')
            invoices_info = utils.PDF_file_read(api_keys, file, pdf_image_path)
        
        if invoices_info:
            for key, value in invoices_info.items():
                invoices_info_list[key].append(value)
            utils.update_label(window, label, f'\n{Path(file).name}')

    if not invoices_info_list:
        messagebox.showerror('Error', 'Could not retrieve invoice information!')
        return

    # _perform_single_lookup(window, label, config, invoices_info)
    lookup_invoices_interactive(window, label, config, invoices_info_list)

        # if not utils.is_driver_active(web_driver):
        #     # Nếu trình duyệt chưa hoạt động (chưa mở hoặc đã đóng), khởi tạo lại
        #     web_driver = web_driver_manager.initialize_web_driver()
        #     if not web_driver: return # Dừng lại nếu khởi tạo thất bại

        # web_driver.get('https://hoadondientu.gdt.gov.vn/')
        # window.attributes('-topmost', False)
        # window.withdraw()

        # WebDriverWait(web_driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.ant-modal-close-x'))).click()

        # utils.web_write(web_driver, By.XPATH, '//*[@id="nbmst"]', HD_info['MST'])
        # utils.web_write(web_driver, By.XPATH, '//*[@id="khhdon"]', HD_info['KHHDon'])
        # utils.web_write(web_driver, By.XPATH, '//*[@id="shdon"]', HD_info['SHDon'])

        # # Xử lý các loại hóa đơn khác nhau
        # if 'TgTThue' not in HD_info or HD_info['TgTThue'] is None: # Không có tiền thuế, hóa đơn bán hàng
        #     web_driver.find_element(By.XPATH, '//*[@id="lhdon"]/div/div').click()
        #     pywinauto.keyboard.send_keys("{DOWN}")  
        #     pywinauto.keyboard.send_keys("{ENTER}")
        # elif int(HD_info['TgTThue']) > 0:
        #     utils.web_write(web_driver, By.XPATH, '//*[@id="tgtthue"]', HD_info['TgTThue'])
            
        # utils.web_write(web_driver, By.XPATH, '//*[@id="tgtttbso"]', HD_info['TgTTTBSo'])

        # # Vòng lặp giải captcha
        # while True:
        #     web_element = WebDriverWait(web_driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".Captcha__Image-sc-1up1k1e-1")))

        #     captcha_path = config.get_temp_file_path('captcha.png')
        #     web_element.screenshot(captcha_path)

        #     response = ai_manager.generate_from_image(
        #         "Extract all characters from this image (this is a captcha code). Return only the character string, say nothing more.",
        #         [captcha_path]
        #     )
        #     # response = utils.AI_generate_content(api_keys, 
        #     #                                "Extract all characters from this image (this is a captcha code). Return only the character string, say nothing more.",
        #     #                                captcha_path,
        #     #                                True)
        #     if not response:
        #         messagebox.showerror("API Error", 'API limit reached or other error occurred.')
        #         window.deiconify() # Hiện lại cửa sổ chính
        #         return

        #     utils.web_write(web_driver, By.XPATH, '//*[@id="cvalue"]', response)

        #     web_driver.find_element(By.CSS_SELECTOR, '.ButtonAnt__Button-sc-p5q16s-0').click()
        #     try:
        #         WebDriverWait(web_driver, 10).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div')))
        #         WebDriverWait(web_driver, 1).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="__next"]/section/main/section/div/div/div/div/div[3]/div[1]/div[2]/div[2]/section/p[1]')))
        #         break # Thoát khỏi vòng lặp nếu thành công
        #     except:
        #         continue # Thử lại nếu captcha sai

        # screenshot_path = config.get_temp_file_path('screenshot.png')
        # image = ImageGrab.grab()
        # image.save(screenshot_path)

        # window.deiconify() # Hiện lại cửa sổ chính
        # window.attributes('-topmost', False)

        # if messagebox.askyesno("Print Confirmation", "Lookup successful. Do you want to print?"):
        #     win32api.ShellExecute(
        #         0,
        #         "print",
        #         screenshot_path, # In file từ đường dẫn tạm
        #         f'/d:"{win32print.GetDefaultPrinter()}"',
        #         ".",
        #         0
        #     )

def _perform_single_lookup(main_window, sub_window, label, config, single_invoice_info, is_reshow_main_window=True):
    # Hàm tra cứu hóa đơn
    try:
        global web_driver

        web_driver_manager = WebDriverManager(main_window, label)

        api_keys = config.get('API_KEY')

        # Khởi tạo trình quản lý AI
        ai_manager = AIManager(api_keys)

        if not utils.is_driver_active(web_driver):
        # Nếu trình duyệt chưa hoạt động (chưa mở hoặc đã đóng), khởi tạo lại
            web_driver = web_driver_manager.initialize_web_driver()
            if not web_driver: return # Dừng lại nếu khởi tạo thất bại

        web_driver.get('https://hoadondientu.gdt.gov.vn/')

        if main_window:
            main_window.attributes('-topmost', False)
            main_window.withdraw()

        if sub_window: sub_window.withdraw()

        WebDriverWait(web_driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.ant-modal-close-x'))).click()

        utils.web_write(web_driver, By.XPATH, '//*[@id="nbmst"]', single_invoice_info['MST'])
        utils.web_write(web_driver, By.XPATH, '//*[@id="khhdon"]', single_invoice_info['KHHDon'])
        utils.web_write(web_driver, By.XPATH, '//*[@id="shdon"]', single_invoice_info['SHDon'])

        # Xử lý các loại hóa đơn khác nhau
        if 'TgTThue' not in single_invoice_info or single_invoice_info['TgTThue'] is None: # Không có tiền thuế, hóa đơn bán hàng
            web_driver.find_element(By.XPATH, '//*[@id="lhdon"]/div/div').click()
            pywinauto.keyboard.send_keys("{DOWN}")  
            pywinauto.keyboard.send_keys("{ENTER}")
        elif int(single_invoice_info['TgTThue']) > 0:
            utils.web_write(web_driver, By.XPATH, '//*[@id="tgtthue"]', single_invoice_info['TgTThue'])
            
        utils.web_write(web_driver, By.XPATH, '//*[@id="tgtttbso"]', single_invoice_info['TgTTTBSo'])

        # Vòng lặp giải captcha
        while True:
            web_element = WebDriverWait(web_driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".Captcha__Image-sc-1up1k1e-1")))

            captcha_path = config.get_temp_file_path('captcha.png')
            web_element.screenshot(captcha_path)

            response = ai_manager.generate_from_image(
                "Extract all characters from this image (this is a captcha code). Return only the character string, say nothing more.",
                [captcha_path]
            )

            if not response:
                messagebox.showerror("API Error", 'API limit reached or other error occurred.')
                if main_window: main_window.deiconify() # Hiện lại cửa sổ chính
                return

            utils.web_write(web_driver, By.XPATH, '//*[@id="cvalue"]', response)

            web_driver.find_element(By.CSS_SELECTOR, '.ButtonAnt__Button-sc-p5q16s-0').click()
            try:
                WebDriverWait(web_driver, 10).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div')))
                WebDriverWait(web_driver, 1).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="__next"]/section/main/section/div/div/div/div/div[3]/div[1]/div[2]/div[2]/section/p[1]')))
                break # Thoát khỏi vòng lặp nếu thành công
            except:
                continue # Thử lại nếu captcha sai

        screenshot_path = config.get_temp_file_path('screenshot.png')
        image = ImageGrab.grab()
        image.save(screenshot_path)
        
        if main_window and is_reshow_main_window:
            main_window.deiconify() # Hiện lại cửa sổ chính
            main_window.attributes('-topmost', False)
        elif sub_window: sub_window.deiconify()

        if messagebox.askyesno("Print Confirmation", "Lookup successful. Do you want to print?"):
            win32api.ShellExecute(
                0,
                "print",
                screenshot_path, # In file từ đường dẫn tạm
                f'/d:"{win32print.GetDefaultPrinter()}"',
                ".",
                0
            )

    except Exception as e:
        print(f"An error occurred in chon_file: {e}")
        if main_window and main_window.state() == 'withdrawn':
            main_window.deiconify() # Đảm bảo cửa sổ chính luôn hiện lại nếu có lỗi
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

def lookup_invoices_interactive(main_window, label, config, invoices_info):
    """
    Call a UI for the user to select an invoice from the defaultdict,
    then triggers the lookup for the selected one.
    
    Args:
        main_window: The main Tkinter window of the application.
        label: The status label to update (if any).
        config: The configuration object.
        HD_info (defaultdict): A defaultdict(list) containing data for multiple invoices.
    """
    # Check if there is any data to process
    if not invoices_info or not invoices_info['Goi']:
        messagebox.showinfo("No Data", "There are no invoices to look up.")
        return
    
    num_invoices = len(invoices_info['Goi'])

    if num_invoices == 1: 
        # Tạo dict cho hóa đơn được chọn từ defaultdict
        single_hd_info = {key: values[0] for key, values in invoices_info.items()}
        _perform_single_lookup(main_window, None, label, config, single_hd_info, True)
        return
    
    # 1. Chuẩn bị danh sách items theo đúng định dạng yêu cầu
    items = []
    for i in range(num_invoices):
        items.append({
            'display': invoices_info['Goi'][i], 
            'value': i             
        })

    # 2. Định nghĩa hàm callback
    def lookup_callback(sub_window, chosen_index):
        # Tạo dict cho hóa đơn được chọn từ defaultdict
        single_hd_info = {key: values[chosen_index] for key, values in invoices_info.items()}
        # Gọi hàm tra cứu thực tế
        _perform_single_lookup(main_window, sub_window, label, config, single_hd_info, False)
    
    # 3. Gọi hàm tạo giao diện chung
    utils.create_selection_gui(
        main_window=main_window,
        title="Chọn hóa đơn để tra cứu",
        items_to_display=items,
        button_text="Tra cứu",
        on_confirm_callback=lookup_callback
    )


        
