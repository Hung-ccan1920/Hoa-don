import sys
import os
import time
import urllib.request
import shutil
import subprocess
import traceback

def wait_for_app_exit(app_path, timeout=10):
    """Chờ file thực thi không còn bị khóa."""
    print("⏳ Đang chờ ứng dụng chính thoát...")
    for _ in range(timeout):
        try:
            os.rename(app_path, app_path)
            print("✅ Ứng dụng chính đã thoát.")
            return True
        except PermissionError:
            time.sleep(1)
        except FileNotFoundError:
            print("✅ Ứng dụng chính đã thoát (không tìm thấy file).")
            return True
    print("❌ Ứng dụng chính chưa thoát sau 10 giây.")
    return False

def download_file(url, output_path):
    """Tải file từ URL với thanh tiến trình."""
    def print_progress_bar(percent, downloaded, total_size, bar_width=20):
        filled = int(percent / 100 * bar_width)
        bar = '█' * filled + '▏' + ' ' * (bar_width - filled - 1)
        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)
        print(f"\r📥 Tải: [{bar}] {percent:5.1f}% ({downloaded_mb:.2f}MB / {total_mb:.2f}MB)", end='', flush=True)

    print(f"🌐 Tải về từ: {url}")
    try:
        with urllib.request.urlopen(url) as response, open(output_path, 'wb') as out_file:
            total_size = int(response.info().get('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                out_file.write(buffer)
                downloaded += len(buffer)
                if total_size:
                    percent = downloaded * 100 / total_size
                    print_progress_bar(percent, downloaded, total_size)
        print("\n✅ Tải xong.")
        return True
    except Exception as e:
        print(f"\n❌ Lỗi khi tải file: {e}")
        return False

def replace_file(target_path, new_file_path, backup=True, restart=False):
    """Thay thế file đích bằng file mới."""
    backup_path = target_path + ".backup"
    try:
        if backup and os.path.exists(target_path):
            print(f"🔐 Sao lưu '{os.path.basename(target_path)}'...")
            if os.path.exists(backup_path): os.remove(backup_path)
            os.rename(target_path, backup_path)

        print(f"♻️ Ghi đè '{os.path.basename(target_path)}'...")
        shutil.move(new_file_path, target_path)

        if restart:
            print(f"🚀 Khởi động lại '{os.path.basename(target_path)}'...")
            process = subprocess.Popen([target_path])
            time.sleep(3)
            if process.poll() is not None:
                print(f"❌ '{os.path.basename(target_path)}' mới bị crash! Đang khôi phục...")
                if os.path.exists(backup_path):
                    os.remove(target_path)
                    os.rename(backup_path, target_path)
                    subprocess.Popen([target_path])
                return False

        # 4. Dọn dẹp file backup sau khi cập nhật thành công
        #    Logic này giờ đã nằm ngoài khối `if restart`
        if backup and os.path.exists(backup_path):
            print(f"🧹 Dọn dẹp file backup...")
            os.remove(backup_path)

        print(f"✅ Cập nhật '{os.path.basename(target_path)}' thành công.")
        return True
    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng khi thay thế: {e}")
        if backup and os.path.exists(backup_path):
            print("↩️ Đang cố gắng khôi phục bản cũ...")
            if os.path.exists(target_path): os.remove(target_path)
            os.rename(backup_path, target_path)
            if restart: subprocess.Popen([target_path])
        return False
    
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

def main():
    if len(sys.argv) != 3:
        print("Lỗi cú pháp! Cách dùng: updater.exe <path_to_target> <download_url>")
        sys.exit(1)

    target_path = sys.argv[1]
    download_url = sys.argv[2]
    temp_file = target_path + ".new"
    
    # Tự động quyết định logic dựa trên tên file
    is_driver_update = os.path.basename(target_path).lower() == 'msedgedriver.exe'

    try:
        # Tải file mới trước
        if not download_file(download_url, temp_file):
            print("❌ Cập nhật thất bại do không thể tải file.")
            sys.exit(1)

        if is_driver_update:
            print("\n=== BẮT ĐẦU CẬP NHẬT MS EDGEDRIVER ===")
            terminate_process(os.path.basename(target_path))
            replace_file(target_path, temp_file, backup=True, restart=False)
        else:
            print("\n=== BẮT ĐẦU CẬP NHẬT ỨNG DỤNG CHÍNH ===")
            if not wait_for_app_exit(target_path):
                #  print("⚠️ Ứng dụng chưa thoát, tắt tiến trình.")
                 terminate_process(os.path.basename(target_path))

            replace_file(target_path, temp_file, backup=True, restart=True)     
    
    except Exception as err:
        print(f"\n❌ Cập nhật thất bại với lỗi không xác định:")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Luôn dọn dẹp file tạm sau khi kết thúc
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    main()