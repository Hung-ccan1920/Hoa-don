from tkinter import messagebox

import google.generativeai as genai
import PIL.Image

# ==============================================================================
# AI MANAGER CLASS
# ==============================================================================

class AIManager:
    """
    Lớp quản lý nội dung AI:
     - Quản lý việc xoay vòng API key.
     - Gửi yêu cầu và xử lý phản hồi từ API của Google Gemini.
    """
    # --- CÁC HẰNG SỐ ---
    _GE_MODEL = "gemini-2.0-flash"

    def __init__(self, api_keys_str):
        self.api_keys_str = api_keys_str
        self.api_keys = api_keys_str.split(',') if api_keys_str else []

    def _attempt_generation(self, prompt, content_parts):
        """
        Lặp qua danh sách API key và thử gửi yêu cầu.
        Nếu thành công, nó trả về kết quả. Nếu tất cả key đều lỗi, nó trả về chuỗi rỗng.
        """
        if not self.api_keys:
            messagebox.showerror("API Key Error", "API Key not found in configuration.")
            return ''

        # Lặp qua từng key trong danh sách để thử, và chỉ thử tối đa 5 lần
        i = 0
        for index, key in enumerate(self.api_keys):
            current_key = key.strip()
            if not current_key:
                continue

            try:
                print(f"Attempting API call with key #{index}...")
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel(model_name=self._GE_MODEL)
                
                # Tạo nội dung yêu cầu hoàn chỉnh
                full_request = [prompt] + content_parts
                response = model.generate_content(full_request)
                return response.text
            
            except Exception as e:
                print(f"Failed with key #{index}. Error: {e}")
                # Nếu lỗi, vòng lặp sẽ tự động tiếp tục với key tiếp theo
                i += 1
                if i >= 5:
                    messagebox.showerror("API Error", "Request limit reached.")
                    return ''
        
        # Nếu vòng lặp kết thúc mà không có key nào thành công
        messagebox.showerror("API Error", "All API keys failed or request limit reached.")
        return ''

    # --- BA HÀM PUBLIC MỚI, RÕ RÀNG VÀ DỄ SỬ DỤNG ---

    def generate_text(self, prompt):
        """Hàm 1: Chỉ gửi một câu lệnh văn bản đơn thuần."""
        # Phần nội dung file là một danh sách rỗng
        return self._attempt_generation(prompt, [])

    def generate_from_image(self, prompt, image_paths: list):
        """Hàm 2: Gửi câu lệnh kèm một hoặc nhiều file ảnh."""
        try:
            pil_images = [PIL.Image.open(path) for path in image_paths]
            # Phần nội dung file là một danh sách chứa đối tượng ảnh
            return self._attempt_generation(prompt, pil_images)
        except FileNotFoundError:
            messagebox.showerror("File Error", f"Image file not found: {image_paths}")
            return ''
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not process image file: {e}")
            return ''

    def generate_from_file(self, prompt, file_path):
        """Hàm 3: Gửi câu lệnh và yêu cầu upload một file (như PDF)."""
        try:
            uploaded_file = genai.upload_file(file_path)
            # Phần nội dung file là một danh sách chứa đối tượng file đã upload
            return self._attempt_generation(prompt, [uploaded_file])
        except FileNotFoundError:
            messagebox.showerror("File Error", f"File not found: {file_path}")
            return ''
        except Exception as e:
            messagebox.showerror("Upload Error", f"Could not upload file: {e}")
            return ''