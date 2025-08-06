import utils
from collections import defaultdict

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

from lxml import etree

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
file_name= ''
IS_WEB_OPENED = False
web_driver = None # Sẽ giữ instance của trình duyệt, None nghĩa là chưa mở


def chon_file(window, label):
    try:
        global file_name, web_driver
        
        file_name = filedialog.askopenfilename(
            # initialdir="/",
            initialdir=file_name.rsplit('/', 1)[0] if file_name else "/",
            title="Chọn file XML hoặc PDF",
            filetypes=( ("XML và PDF files", "*.xml *.pdf"), ("all files", "*.*"))
        )

        if not file_name: # Nếu người dùng hủy, không làm gì cả
            return

        label.config(text=file_name)

        if '.xml' in file_name:
            HD_info = utils.XML_file_read(file_name,False)
        else:
            HD_info = utils.PDF_file_read(file_name)

        if not HD_info:
            #messagebox.showerror('Lỗi', 'Không có thông tin hóa đơn!')
            return

        # --- Quản lý trình duyệt và tải trang thông minh ---
        target_url = 'https://hoadondientu.gdt.gov.vn/'
        try:
            # Kiểm tra xem trình duyệt có đang chạy không.
            # Việc truy cập một thuộc tính như .title sẽ báo lỗi nếu trình duyệt đã bị đóng.
            _ = web_driver.title
            
            # Nếu trình duyệt đang chạy, kiểm tra URL hiện tại
            if web_driver.current_url.startswith(target_url):
                web_driver.refresh() # Nếu đã ở đúng trang, chỉ cần làm mới
            else:
                web_driver.get(target_url) # Nếu ở trang khác, điều hướng tới
        except Exception:
            # Lỗi xảy ra nếu edge_driver là None hoặc trình duyệt đã bị đóng.
            # Khởi tạo một trình duyệt mới.
            # edge_service, edge_options = utils.initialize_web_driver()
            web_driver = utils.initialize_web_driver(window, label)
            web_driver.get(target_url)

        # Bỏ chế độ ontop khi mở trang web
        window.attributes('-topmost', False)
        window.withdraw()

        # tắt popup
        WebDriverWait(web_driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.ant-modal-close-x'))).click()

        utils.web_write(web_driver, By.XPATH, '//*[@id="nbmst"]', HD_info['MST'])
        utils.web_write(web_driver, By.XPATH, '//*[@id="khhdon"]', HD_info['KHHDon'])
        utils.web_write(web_driver, By.XPATH, '//*[@id="shdon"]', HD_info['SHDon'])

        if not (tax := HD_info['TgTThue']) : # không có tiền thuế, là hóa đơn bán hàng
            web_driver.find_element(By.XPATH, '//*[@id="lhdon"]/div/div').click()
            pywinauto.keyboard.send_keys("{DOWN}")  
            pywinauto.keyboard.send_keys("{ENTER}")
        elif tax > 0: # thuế âm thì không cần nhập
            utils.web_write(web_driver, By.XPATH, '//*[@id="tgtthue"]', tax)
            

        utils.web_write(web_driver, By.XPATH, '//*[@id="tgtttbso"]', HD_info['TgTTTBSo'])

        while True:
            # Lấy mã captcha
            web_element = WebDriverWait(web_driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".Captcha__Image-sc-1up1k1e-1")))
            # Lưu mã captcha thành file ảnh
            web_element.screenshot('captcha.png')

            response = utils.AI_generate_content("Trích xuất tất cả ký tự trong hình ảnh này (đây là mã captcha), chỉ trả về chuỗi ký tự, không nói gì thêm.",
                                            'captcha.png',
                                            True)
            # Kiểm tra respond, nếu rỗng thì ngừng lại
            if not response:
                messagebox.showerror("Lỗi gởi yêu cầu", 'Hết hạn mức gởi yêu cầu hoặc lỗi API')
                window.iconify()
                return # Thoát khỏi hàm ngay lập tức, không thực hiện các dòng mã sau

            # Điền mã captcha vào ô nhập liệu
            utils.web_write(web_driver, By.XPATH, '//*[@id="cvalue"]', response)

            #Bấm nút tra cứu
            web_driver.find_element(By.CSS_SELECTOR, '.ButtonAnt__Button-sc-p5q16s-0').click()
            try:
                # lớp phủ biến mất đi khi tải xong
                WebDriverWait(web_driver, 10).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div')))

                # Tìm thông báo đã tra cứu được hóa đơn có chưa
                WebDriverWait(web_driver, 1).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="__next"]/section/main/section/div/div/div/div/div[3]/div[1]/div[2]/div[2]/section/p[1]')))
                # Nếu có, đã tra cứu được, thoát vòng lặp. Nếu không sẽ bị lỗi exception
                window.iconify()
                break
            except:
                None # Tiếp tục vòng lặp

        # Chụp toàn bộ màn hình
        image = ImageGrab.grab()
        image.save('screenshot.png')

        # Đặt cửa sổ luôn ở trên cùng
        window.iconify()
        window.attributes('-topmost', True)

        in_khong = messagebox.askquestion("Thông báo", "Đã tra cứu xong. Bạn có muốn in không?")

        if in_khong == 'yes':
                # In ảnh bằng máy in mặc định
            win32api.ShellExecute(
                0,
                "print",
                'screenshot.png',
                '/d:"%s"' % win32print.GetDefaultPrinter(),
                ".",
                0
            )
    
    except Exception as e:
        print("Lỗi hàm chọn file", f"Lỗi: {e}")
        window.iconify()









