import base64
import utils


# Khóa cho mã hóa Caesar (một số nguyên)
# Bạn nên thay đổi giá trị này để tăng tính bảo mật (một chút)
CAESAR_KEY = 9
ENCRYPTION_MARKER = "ENC"

def caesar_cipher(text, key, decrypt=False):
    """Mã hóa hoặc giải mã văn bản bằng Caesar cipher."""
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            start = ord('a')
            shifted_char = chr((ord(char) - start + (key if not decrypt else -key)) % 26 + start)
        elif 'A' <= char <= 'Z':
            start = ord('A')
            shifted_char = chr((ord(char) - start + (key if not decrypt else -key)) % 26 + start)
        elif '0' <= char <= '9':
            start = ord('0')
            shifted_char = chr((ord(char) - start + (key if not decrypt else -key)) % 10 + start)
        else:
            shifted_char = char # Giữ nguyên các ký tự khác
        result.append(shifted_char)
    return "".join(result)

def encrypt_password(password):
    """Mã hóa mật khẩu: Caesar cipher rồi Base64 encode."""
    if password.startswith(ENCRYPTION_MARKER): # Đã mã hóa rồi thì không mã hóa nữa
        return password
    # 1. Áp dụng Caesar cipher
    caesar_encrypted = caesar_cipher(password, CAESAR_KEY)
    # 2. Mã hóa Base64
    base64_encrypted = base64.b64encode(caesar_encrypted.encode('utf-8')).decode('utf-8')
    return ENCRYPTION_MARKER + base64_encrypted

def decrypt_password(encrypted_password):
    """Giải mã mật khẩu: Base64 decode rồi Caesar decipher."""
    if not encrypted_password.startswith(ENCRYPTION_MARKER):
        # Nếu không có marker, có thể là mật khẩu gốc chưa mã hóa
        # hoặc định dạng không đúng. Tạm thời trả về nguyên bản.
        # Trong thực tế, bạn cần xử lý trường hợp này cẩn thận hơn.
        return encrypted_password

    actual_encrypted_password = encrypted_password[len(ENCRYPTION_MARKER):]
    try:
        # 1. Giải mã Base64
        base64_decoded = base64.b64decode(actual_encrypted_password.encode('utf-8')).decode('utf-8')
        # 2. Giải mã Caesar cipher
        decrypted_text = caesar_cipher(base64_decoded, CAESAR_KEY, decrypt=True)
        return decrypted_text
    except Exception as e:
        print(f"Lỗi giải mã: {e}. Có thể mật khẩu không được mã hóa đúng cách.")
        return None # Hoặc trả về actual_encrypted_password nếu muốn
def password_manager():
    '''Hàm mã hóa mật khẩu và lưu vào file config.txt'''
    # Mã hóa mật khẩu
    passwords = utils.config_file_value('password')
    
    if passwords:
        # Mã hóa và tạo danh sách các phần đã mã hóa bằng list comprehension
        encrypted_parts = [encrypt_password(password) for password in passwords]
        # Nối lại
        encrypt_passwords = ",".join(encrypted_parts)
        # Ghi vào file config
        utils.write_config_file('password', encrypt_passwords)
