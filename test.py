import os
import subprocess

def kiem_tra_phien_ban_edge_va_driver(duong_dan_msedgedriver):
    """
    Kiểm tra và so sánh phiên bản của Microsoft Edge và msedgedriver.exe.

    Args:
        duong_dan_msedgedriver (str): Đường dẫn đầy đủ đến tệp msedgedriver.exe.

    Returns:
        tuple: Một tuple chứa (phien_ban_edge, phien_ban_driver, ket_qua_so_sanh).
               ket_qua_so_sanh có thể là:
               - "Khớp"
               - "Không khớp"
               - "Không tìm thấy Edge"
               - "Không tìm thấy msedgedriver"
    """
    phien_ban_edge = None
    phien_ban_driver = None
    ket_qua_so_sanh = ""

    # --- Lấy phiên bản Microsoft Edge đã cài đặt trên Windows ---
    try:
        # Sử dụng lệnh PowerShell để lấy thông tin phiên bản từ registry
        cmd = r'(Get-AppxPackage Microsoft.MicrosoftEdge).Version'
        ket_qua_powershell = subprocess.check_output(["powershell", "-Command", cmd],
                                                     stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                                                     universal_newlines=True, shell=True)
        phien_ban_edge = ket_qua_powershell.strip().split('.')[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        phien_ban_edge = "Không tìm thấy"
        ket_qua_so_sanh = "Không tìm thấy Edge"

    # --- Lấy phiên bản của msedgedriver.exe ---
    if os.path.exists(duong_dan_msedgedriver):
        try:
            # Chạy lệnh `msedgedriver.exe --version`
            ket_qua_driver = subprocess.check_output([duong_dan_msedgedriver, "--version"],
                                                   universal_newlines=True)
            # Tách chuỗi để lấy số phiên bản chính, ví dụ: "MSEdgeDriver 127.0.2651.92" -> "127"
            phien_ban_driver = ket_qua_driver.split(' ')[1].split('.')[0]
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            phien_ban_driver = "Lỗi khi đọc phiên bản"
            ket_qua_so_sanh = "Lỗi khi đọc phiên bản driver"
    else:
        phien_ban_driver = "Không tìm thấy"
        ket_qua_so_sanh = "Không tìm thấy msedgedriver"

    # --- So sánh phiên bản chính (major version) ---
    if phien_ban_edge and phien_ban_driver and not ket_qua_so_sanh:
        if phien_ban_edge == phien_ban_driver:
            ket_qua_so_sanh = "Khớp 👍"
        else:
            ket_qua_so_sanh = "Không khớp 👎"

    return phien_ban_edge, phien_ban_driver, ket_qua_so_sanh

def terminate_process(process_name):
    """
    Buộc một tiến trình phải tắt bằng tên của nó.
    
    Args:
        process_name (str): Tên của file thực thi (ví dụ: "msedgedriver.exe").
    """
    try:
        print(f"Đang tìm và tắt tiến trình: {process_name}...")
        # Lệnh taskkill của Windows:
        # /F: Buộc tắt (Force)
        # /IM: Chỉ định tên tiến trình (Image Name)
        # /T: Tắt cả các tiến trình con
        command = ["taskkill", "/F", "/IM", process_name, "/T"]
        
        # Chạy lệnh và ẩn cửa sổ dòng lệnh
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print(f"✅ Đã tắt thành công {process_name}.")
        elif "process not found" in result.stderr.lower():
            print(f"ℹ️ Không tìm thấy tiến trình {process_name} đang chạy.")
        else:
            print(f"⚠️ Không thể tắt {process_name}. Lỗi: {result.stderr}")
            
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy lệnh 'taskkill'. Đây không phải là môi trường Windows.")
    except Exception as e:
        print(f"Lỗi không xác định khi tắt tiến trình: {e}")


# --- CÁCH SỬ DỤNG ---
if __name__ == "__main__":
    # # THAY ĐỔI ĐƯỜNG DẪN NÀY đến tệp msedgedriver.exe của bạn
    # duong_dan_driver = r"F:\OneDrive\Python\msedgedriver.exe"

    # edge_ver, driver_ver, ket_qua = kiem_tra_phien_ban_edge_va_driver(duong_dan_driver)

    # print(f"Phiên bản Microsoft Edge: {edge_ver}")
    # print(f"Phiên bản msedgedriver.exe: {driver_ver}")
    # print("-----------------------------------------")
    # print(f"Kết quả so sánh: {ket_qua}")
    terminate_process('msedgedriver.exe')