import utils
from ai_manager import AIManager
from web_driver_manager import WebDriverManager

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options  
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.microsoft import EdgeChromiumDriverManager

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

import os
import google.generativeai as genai
from PIL import ImageGrab
import PIL.Image
import time
import win32api
import win32print
import fitz 
import pywinauto


# Biến toàn cục 
file_name = ''
web_driver = None # Giữ instance của trình duyệt

def chon_file(window, label, config):
    """
    Hàm chính xử lý logic tra cứu hóa đơn.
    """
    try:
        global file_name, web_driver

        web_driver_manager = WebDriverManager(window, label)

        file_name = filedialog.askopenfilename(
            initialdir=file_name.rsplit('/', 1)[0] if file_name else "/",
            title="Select XML or PDF file",
            filetypes=(("XML and PDF files", "*.xml *.pdf"), ("all files", "*.*"))
        )

        if not file_name: # Nếu người dùng hủy
            return

        label.config(text=file_name)

        api_keys = config.get('API_KEY')

        # Khởi tạo trình quản lý AI
        ai_manager = AIManager(api_keys)

        if '.xml' in file_name:
            HD_info = utils.XML_file_read(api_keys, file_name, False)
        else:
            # <<< THAY ĐỔI 3: Sử dụng thư mục tạm
            pdf_image_path = config.get_temp_file_path('pdf.png')
            HD_info = utils.PDF_file_read(api_keys, file_name, pdf_image_path)

        if not HD_info:
            messagebox.showerror('Error', 'Could not retrieve invoice information!')
            return

        
        if not utils.is_driver_active(web_driver):
            # Nếu trình duyệt chưa hoạt động (chưa mở hoặc đã đóng), khởi tạo lại
            web_driver = web_driver_manager.initialize_web_driver()
            if not web_driver: return # Dừng lại nếu khởi tạo thất bại

        web_driver.get('https://hoadondientu.gdt.gov.vn/')
        window.attributes('-topmost', False)
        window.withdraw()

        WebDriverWait(web_driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.ant-modal-close-x'))).click()

        utils.web_write(web_driver, By.XPATH, '//*[@id="nbmst"]', HD_info['MST'])
        utils.web_write(web_driver, By.XPATH, '//*[@id="khhdon"]', HD_info['KHHDon'])
        utils.web_write(web_driver, By.XPATH, '//*[@id="shdon"]', HD_info['SHDon'])

        # Xử lý các loại hóa đơn khác nhau
        if 'TgTThue' not in HD_info or HD_info['TgTThue'] is None:
            web_driver.find_element(By.XPATH, '//*[@id="lhdon"]/div/div').click()
            pywinauto.keyboard.send_keys("{DOWN}")  
            pywinauto.keyboard.send_keys("{ENTER}")
        elif int(HD_info['TgTThue']) > 0:
            utils.web_write(web_driver, By.XPATH, '//*[@id="tgtthue"]', HD_info['TgTThue'])
            
        utils.web_write(web_driver, By.XPATH, '//*[@id="tgtttbso"]', HD_info['TgTTTBSo'])

        # Vòng lặp giải captcha
        while True:
            web_element = WebDriverWait(web_driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".Captcha__Image-sc-1up1k1e-1")))

            captcha_path = config.get_temp_file_path('captcha.png')
            web_element.screenshot(captcha_path)

            response = ai_manager.generate_from_image(
                "Extract all characters from this image (this is a captcha code). Return only the character string, say nothing more.",
                [captcha_path]
            )
            # response = utils.AI_generate_content(api_keys, 
            #                                "Extract all characters from this image (this is a captcha code). Return only the character string, say nothing more.",
            #                                captcha_path,
            #                                True)
            if not response:
                messagebox.showerror("API Error", 'API limit reached or other error occurred.')
                window.deiconify() # Hiện lại cửa sổ chính
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

        window.deiconify() # Hiện lại cửa sổ chính
        window.attributes('-topmost', False)

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
        if window.state() == 'withdrawn':
            window.deiconify() # Đảm bảo cửa sổ chính luôn hiện lại nếu có lỗi
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")