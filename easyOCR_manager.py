import easyocr
import os
import time
from concurrent.futures import ThreadPoolExecutor

class EasyOCRManager:
    """
    Một lớp để quản lý việc khởi tạo EasyOCR trong một luồng nền.
    """
    def __init__(self, languages=['en'], model_directory='easyocr_model', gpu=False):
        """
        Khởi tạo và bắt đầu quá trình tải model trong nền.
        """
        self.reader = None
        self.status = "INITIALIZING" # Trạng thái: INITIALIZING, READY, FAILED
        self.languages = languages
        self.model_directory = model_directory
        self.gpu = gpu

        print(f"[{time.strftime('%H:%M:%S')}] Starting OCR initialization")
        self.initialize()

    def _load_model(self):
        """
        Đây là hàm chạy trong luồng ẩn.
        Nó thực hiện công việc nặng nhọc: tải và nạp model.
        """
        print(f"[{time.strftime('%H:%M:%S')}] Loading model...")
        # os.makedirs(self.model_directory, exist_ok=True)
        try:
            # Nếu model đã có, nó sẽ nạp rất nhanh.
            # Nếu chưa có, nó sẽ tự động tải về ở đây.
            reader_instance = easyocr.Reader(
                self.languages,
                model_storage_directory=self.model_directory,
                gpu=self.gpu
            )
            print(f"[{time.strftime('%H:%M:%S')}] Model loaded successfully.")
            return reader_instance
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Failed to load model. Error: {e}")
            return e # Trả về lỗi nếu có

    def _on_load_complete(self, future):
        """
        Đây là hàm callback, được tự động gọi khi luồng ẩn hoàn thành.
        """
        result = future.result()
        if isinstance(result, easyocr.Reader):
            self.reader = result
            self.status = "READY"
            print(f"[{time.strftime('%H:%M:%S')}] OCR system is now READY.")
        else: # Nếu kết quả là một lỗi
            self.status = "FAILED"
            print(f"[{time.strftime('%H:%M:%S')}] OCR system failed to initialize.")


    def initialize(self):
        """
        Kiểm tra folder chứa model có hay chưa, nếu có thì nạp model trực tiếp, nếu không thì tạo luồng để tải model background.
        Sử dụng ThreadPoolExecutor để chạy hàm _load_model và đính kèm hàm callback.
        """
        if os.path.exists(self.model_directory) and os.listdir(self.model_directory):
            self.reader = self._load_model()
            self.status = "READY"
        else:
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(self._load_model)
            future.add_done_callback(self._on_load_complete)
            executor.shutdown(wait=False) # Không chờ luồng hoàn thành

    def process_image(self, image_path):
        """
        Hàm công khai để xử lý ảnh. Sẽ kiểm tra trạng thái trước khi chạy.
        """
        if self.status == "READY":
            print(f"\nProcessing image: {image_path}")
            # Dùng self.reader đã được khởi tạo để xử lý
            return self.reader.readtext(image_path)
        elif self.status == "INITIALIZING":
            print("\nOCR system is still initializing, please wait.")
            return ''
        else: # self.status == "FAILED"
            print("\nOCR system failed to initialize. Cannot process image.")
            return ''