from ai_manager import AIManager

from collections import defaultdict
import os
import sys
import re
from datetime import datetime
import glob

# --- Các thư viện giao diện và web ---
from tkinter import messagebox
from selenium.common.exceptions import WebDriverException
import fitz 

from lxml import etree

import tkinter as tk
from tkinter import ttk

def center_window(window, width, height):
    """Canh giữa một cửa sổ (Tk hoặc Toplevel) trên màn hình."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x_pos = (screen_width // 2) - (width // 2)
    y_pos = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}{"x"}{height}+{x_pos}+{y_pos}")

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

def XML_file_read(api_keys, file_name, is_use_AI)->defaultdict:
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
    
    if is_use_AI:
        ai_manager = AIManager(api_keys)
        response = ai_manager.generate_text(f'Tìm kiếm thông tin trong nội dung hóa đơn sau: {contract_info} '
                                'và trả về thông tin theo từng dòng các nội dung sau: '
                                'Số hợp đồng: [giá trị]'
                                'Ngày hợp đồng: [giá trị]'
                                'Tên gói : [giá trị].'
                                'Qui tắc:'
                                '- Chỉ trả về 3 dòng thông tin như trên. Không thêm lời chào, giải thích, ghi chú hay bất kỳ ký tự thừa nào. Giá trị nào không có thì để chuỗi rỗng'
                                '- chuyển đổi ngày tháng sang định dạng dd/MM/yyyy'
                                '- Số hợp đồng: trong nội dung hóa đơn, ví dụ 406/HD-TTMLMN'
                                '- Tên gói: bước 1: tìm loại hình công việc trong phần nội dung hóa đơn, chuyển thành mã viết tắt: nếu có nội dung tư vấn thiết kế hoặc lập phương án thì thêm mã TVTK, tư vấn thẩm tra thì thêm mã TVTT, giám sát thì thêm mã TVGS, sữa chữa thì thêm mã SCCT, thi công thì thêm mã TC. Bước 2: tìm mã gói thầu đi kèm (thường có chuỗi ký tự và số, ví dụ 24BDCF-TA). Bước 3 kết hợp lại theo quy tắc [Mã viết tắt] [Mã gói thầu] (ví dụ SCCT 24BDCF-TA)')
        
        # response = AI_generate_content(api_keys, 
        #                         f'Tìm kiếm thông tin trong nội dung hóa đơn sau: {contract_info} '
        #                         'và trả về thông tin theo từng dòng các nội dung sau: '
        #                         'Số hợp đồng: [giá trị]'
        #                         'Ngày hợp đồng: [giá trị]'
        #                         'Tên gói : [giá trị].'
        #                         'Qui tắc:'
        #                         '- Chỉ trả về 3 dòng thông tin như trên. Không thêm lời chào, giải thích, ghi chú hay bất kỳ ký tự thừa nào. Giá trị nào không có thì để chuỗi rỗng'
        #                         '- chuyển đổi ngày tháng sang định dạng dd/MM/yyyy'
        #                         '- Số hợp đồng: trong nội dung hóa đơn, ví dụ 406/HD-TTMLMN'
        #                         '- Tên gói: bước 1: tìm loại hình công việc trong phần nội dung hóa đơn, chuyển thành mã viết tắt: nếu có nội dung tư vấn thiết kế hoặc lập phương án thì thêm mã TVTK, tư vấn thẩm tra thì thêm mã TVTT, giám sát thì thêm mã TVGS, sữa chữa thì thêm mã SCCT, thi công thì thêm mã TC. Bước 2: tìm mã gói thầu đi kèm (thường có chuỗi ký tự và số, ví dụ 24BDCF-TA). Bước 3 kết hợp lại theo quy tắc [Mã viết tắt] [Mã gói thầu] (ví dụ SCCT 24BDCF-TA)',
        #                         None,
        #                         False)
        if not response:
            messagebox.showerror('XML_file_read Error', 'Quota Exceeded')
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
        if thong_tin['NHDong']:
            thong_tin['NHDong'] = datetime.strptime(thong_tin['NHDong'], "%d/%m/%Y").strftime("%Y/%m/%d")
    else:
        # Loại bỏ phần phụ lục khỏi chuỗi, xử lý cả "phụ lục" và "Phụ lục"
        contract_info = re.sub(r", (phụ|Phụ) lục.*", "", contract_info, flags=re.IGNORECASE)

        # Sử dụng regular expression để tìm số hợp đồng (bao gồm cả "HĐ")
        so_hop_dong_match = re.search(r"(?:HĐ số|hợp đồng số:)\s*(\d+\/[\w\.-]+)", contract_info)
        thong_tin['SHDong'] = so_hop_dong_match.group(1) if so_hop_dong_match else 'None'

        # Sử dụng regular expression để tìm ngày hợp đồng
        ngay_hop_dong_match = re.search(r"ngày (\d{2}/\d{2}/\d{4})", contract_info)
        
        if ngay_hop_dong_match:
            HD_date = datetime.strptime(ngay_hop_dong_match.group(1), "%d/%m/%Y").strftime("%Y/%m/%d")
        else:
            HD_date = ''

        thong_tin['NHDong'] = HD_date

        # Tìm loại công việc dựa vào từ khóa
        loai_cong_viec = ''
        if "khảo sát" in contract_info.lower() or "thiết kế" in contract_info.lower() or "tư vấn thiết kế" in contract_info.lower():
            loai_cong_viec = "TVTK"
        if "thẩm tra" in contract_info.lower():
            loai_cong_viec = "TVTT"
        if "giám sát" in contract_info.lower():
            loai_cong_viec = "TVGS"
        if "sửa chữa" in contract_info.lower() or "cải tạo" in contract_info.lower():
            loai_cong_viec = "SCCT"
        if "thi công" in contract_info.lower():
            loai_cong_viec = "TC"

        # Sử dụng regular expression để tìm chuỗi đặc biệt
        chuoi_dac_biet_match = re.search(r"(\d{2}[A-Z]{2,}[A-Z\d-]{2,})", contract_info)
        chuoi_dac_biet = chuoi_dac_biet_match.group(1) if chuoi_dac_biet_match else 'None'

        thong_tin['Goi'] = f'{loai_cong_viec} {chuoi_dac_biet}'

    thong_tin['LinkTC']= ''
    thong_tin['MaTC']= ''

    return thong_tin

def PDF_file_read(api_keys, file_name, pdf_image_path)->defaultdict:
    ''' Đọc file PDF và truy xuất giá trị, trả về thông tin hóa đơn''' 

    # Chuyển file PDF thành hình ảnh để gửi Gemini phân tích
    #Mở file PDF
    image_paths = convert_pdf_to_images(file_name, pdf_image_path)

     # Kiểm tra xem có ảnh nào được tạo ra không
    if not image_paths:
        messagebox.showerror("PDF Error", "Could not convert PDF to images.")
        return {}

    
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
    ai_manager = AIManager(api_keys)
    response = ai_manager.generate_from_image('Bạn là một trợ lý AI chuyên về xử lý và trích xuất dữ liệu từ hình ảnh hóa đơn điện tử của Việt Nam, Bạn phân tích hình ảnh hóa đơn được cung cấp và trả về thông tin một cách chính xác theo đúng định dạng và các quy tắc được nêu dưới đây: '
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
                            image_paths)            
    if not response:
        messagebox.showerror('PDF_file_read Error', 'Quota Exceeded')
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
    
def get_app_path():
    """Trả về đường dẫn đến thư mục gốc của ứng dụng (.py hoặc .exe)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(sys.argv[0]))

def find_file(file_name):
    """
    Tìm kiếm một file trong thư mục gốc của ứng dụng và các thư mục con.
    Hàm này giờ độc lập và không cần config.
    """
    app_dir = get_app_path()
    for root, dirs, files in os.walk(app_dir):
        dirs[:] = [d for d in dirs if not d.startswith('_')] # Bỏ không tìm các  thư mục nội bộ
        if file_name in files:
            return os.path.join(root, file_name)
    return None

def is_driver_active(driver):
    """
    Kiểm tra xem một instance của WebDriver có đang hoạt động hay không.
    Trả về True nếu driver tồn tại và cửa sổ trình duyệt đang mở.
    Trả về False nếu driver là None hoặc cửa sổ đã bị đóng.
    """
    # Trường hợp 1: Driver chưa bao giờ được khởi tạo
    if driver is None:
        return False
    
    # Trường hợp 2: Driver đã được khởi tạo, kiểm tra xem nó còn sống không
    try:
        # Lệnh .title là một cách nhẹ nhàng để kiểm tra kết nối với trình duyệt.
        # Nếu trình duyệt đã bị đóng, lệnh này sẽ gây ra lỗi WebDriverException.
        _ = driver.title
        return True
    except WebDriverException:
        # Nếu có lỗi, nghĩa là người dùng đã đóng cửa sổ trình duyệt
        return False
    
def convert_pdf_to_images(pdf_path, output_prefix, dpi=150):
    """
    Chuyển đổi TẤT CẢ các trang của một file PDF thành các file hình ảnh.

    Args:
        pdf_path (str): Đường dẫn đến file PDF đầu vào.
        output_prefix (str): Tiền tố cho các file ảnh đầu ra.
                             Ví dụ: 'C:/temp/invoice' sẽ tạo ra
                             'C:/temp/invoice-p0.png', 'C:/temp/invoice-p1.png', ...
        dpi (int): Độ phân giải của ảnh, mặc định là 150.

    Returns:
        list: Một danh sách các đường dẫn đến file ảnh đã được tạo.
    """
    image_paths = []
    try:
        # Mở file PDF
        doc = fitz.open(pdf_path)
        
        # Lặp qua từng trang trong tài liệu
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)  # Tải trang hiện tại
            pix = page.get_pixmap(dpi=dpi)
            
            # Tạo đường dẫn file ảnh duy nhất cho mỗi trang
            image_path = f"{output_prefix}-p{page_num}.png"
            pix.save(image_path)
            image_paths.append(image_path)
            
        print(f"Successfully converted {doc.page_count} pages from '{os.path.basename(pdf_path)}'.")
        return image_paths
        
    except Exception as e:
        print(f"An error occurred while converting PDF: {e}")
        return []
    
def process_data_from_vba(keys, raw_string: str) -> defaultdict:
    """
    Parses the pipe-and-comma delimited string from VBA into a defaultdict(list).
    
    Args:
        raw_string: The raw data string passed from the VBA macro.
    
    Returns:
        A defaultdict containing lists of invoice data.
    """
    # Initialize a defaultdict with a list factory.
    # When a new key is accessed, it's automatically created with an empty list.
    invoice_data = defaultdict(list)

    # Split the raw string by "|" to get a list of individual invoice strings
    invoice_list = raw_string.split('|')

    # Iterate over each invoice string
    for invoice_str in invoice_list:
        # Split each invoice string by "," to get the fields
        fields = invoice_str.split(',')
        
        # Ensure the data is well-formed and has the correct number of fields
        if len(fields) == len(keys):
            # Use zip to efficiently pair each key with its corresponding value
            for key, value in zip(keys, fields):
                # Append the value to the correct list within the defaultdict
                invoice_data[key].append(value)
        else:
            # Print a warning for any malformed data row
            print(f"Warning: Skipping malformed data row: {invoice_str}")
            
    return invoice_data

def create_selection_gui(main_window, title, items_to_display, button_text, on_confirm_callback):
    """
    Tạo một giao diện lựa chọn chung với các radio button và một nút xác nhận.

    Args:
        main_window: Cửa sổ chính của ứng dụng.
        title (str): Tiêu đề của cửa sổ lựa chọn.
        items_to_display (list): Một danh sách các mục để hiển thị. 
                                 Mỗi mục là một dict {'display': str, 'value': any}.
                                 'display' là văn bản hiển thị, 'value' là giá trị trả về khi được chọn.
        button_text (str): Văn bản cho nút xác nhận.
        on_confirm_callback (function): Hàm sẽ được gọi khi nút được nhấn. 
                                        Hàm này sẽ nhận một tham số: giá trị 'value' của mục được chọn.
    """
    if main_window:
        # Nếu có cửa sổ chính, ẩn nó đi và tạo cửa sổ phụ Toplevel
        main_window.withdraw()
        sub_window = tk.Toplevel(main_window)
    else:
        # Nếu không có cửa sổ chính (chạy độc lập từ VBA),
        # tạo cửa sổ này như một cửa sổ gốc Tk() và ẩn cửa sổ gốc mặc định có thể xuất hiện
        # bằng cách tạo một root riêng và ẩn nó đi.
        root = tk.Tk()
        root.withdraw()
        sub_window = tk.Toplevel(root)

    sub_window.title(title)

    # --- Thiết lập dark mode  ---
    sub_window.configure(bg="#2e2e2e")
    style = ttk.Style(sub_window)
    style.theme_use('clam')
    style.configure(".", background="#2e2e2e", foreground="white")
    style.configure("TRadiobutton", background="#2e2e2e", foreground="white", font=("Arial", 10), padding=5)
    style.configure("TButton", background="#444444", foreground="white", font=("Arial", 10, "bold"))
    style.map("TButton", background=[("active", "#555555")])
    style.map("TRadiobutton",background=[('active', '#555555')])

    # --- Tạo các thành phần giao diện ---
    # Biến để lưu giá trị 'value' của radio button được chọn
    selected_value = tk.Variable(value=items_to_display[0]['value'])

    frame_radio = ttk.Frame(sub_window, padding="10 10 10 10")
    frame_radio.pack(fill="both", expand=True)

    # Tạo các radio button từ danh sách items_to_display
    for item in items_to_display:
        radio = ttk.Radiobutton(
            frame_radio, 
            text=item['display'], 
            variable=selected_value, 
            value=item['value']
        )
        radio.pack(anchor="w", padx=5)

    def handle_confirm():
        """Hàm xử lý khi nút xác nhận được nhấn."""
        chosen_value = selected_value.get()
        # sub_window.withdraw()
        on_confirm_callback(chosen_value) # Gọi hàm callback với giá trị đã chọn

    confirm_button = ttk.Button(
        sub_window, 
        text=button_text, 
        style="TButton", 
        command=handle_confirm
    )
    confirm_button.pack(pady=10, padx=10, fill="x")

    def on_closing():
        """Hàm xử lý khi cửa sổ bị đóng."""
        sub_window.destroy()
        if main_window: main_window.deiconify()
        else: root.destroy()  # Đóng cửa sổ gốc nếu không có cửa sổ chính


    sub_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Tự động điều chỉnh kích thước và căn giữa
    sub_window.update_idletasks()
    center_window(sub_window, sub_window.winfo_width() + 40, sub_window.winfo_height())
    # sub_window.transient(main_window)
    # sub_window.grab_set()
    sub_window.wait_window() # Đợi cho đến khi cửa sổ này được đóng

    # sub_window.mainloop()