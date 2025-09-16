import cv2
import numpy as np
import os

def find_puzzle_gap_x_coordinate(background_image_path, pixel_count_threshold=30):
    """
    Phân tích ảnh nền captcha để tìm vị trí x của ô trống.
    Hàm này sẽ lưu lại các bước xử lý ảnh để dễ dàng debug.

    Args:
        background_image_path (str): Đường dẫn đến file ảnh nền (bg.png).
        pixel_count_threshold (int): Ngưỡng số pixel sáng màu để xác định một cạnh.

    Returns:
        int: Tọa độ x của cạnh trái ô trống, hoặc None nếu không tìm thấy.
    """
    # Tạo thư mục để lưu các bước xử lý ảnh
    output_dir = "debug_images"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # --- BƯỚC 1: Đọc ảnh và chuyển sang ảnh xám ---
        background_img = cv2.imread(background_image_path)
        if background_img is None:
            print("Error: Could not read the background image.")
            return None
            
        gray_img = cv2.cvtColor(background_img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(os.path.join(output_dir, "step1_grayscale.png"), gray_img)
        print("Saved: step1_grayscale.png")

        # --- BƯỚC 2: Áp dụng Phân ngưỡng Nhị phân để tạo ảnh đen/trắng ---
        # Ngưỡng 127 là giá trị trung bình, có thể điều chỉnh nếu cần.
        # cv2.THRESH_BINARY_INV sẽ làm cho ô trống màu đen và nền màu trắng, dễ nhìn hơn.
        _, binary_img = cv2.threshold(gray_img, 210, 255, cv2.THRESH_BINARY)
        cv2.imwrite(os.path.join(output_dir, "step2_binary.png"), binary_img)
        print("Saved: step2_binary.png")
        
        # --- BƯỚC 3: Quét ảnh từ trái sang phải để tìm cạnh ---
        height, width = binary_img.shape
        
        # Bỏ qua 60 pixel đầu tiên vì đó là vị trí của miếng ghép ban đầu
        start_x = 66 
        
        print(f"Scanning image from x={start_x} to x={width}...")
        
        # Lặp qua từng cột pixel theo chiều rộng
        for x in range(start_x, width):
            # Lấy ra một dải ảnh dọc tại vị trí x
            vertical_strip = binary_img[:, x]
            
            # Đếm số pixel trắng (giá trị > 0) trong dải ảnh đó
            white_pixel_count = np.count_nonzero(vertical_strip)
            
            # In ra để theo dõi (bạn có thể bỏ comment dòng này để xem chi tiết)
            # if white_pixel_count > 10: print(f"Column x={x}, White Pixels={white_pixel_count}")

            # Nếu số pixel trắng vượt ngưỡng, chúng ta đã tìm thấy cạnh
            if white_pixel_count >= pixel_count_threshold:
                print(f"--> Edge found at x = {x} with {white_pixel_count} white pixels (threshold was {pixel_count_threshold}).")
                
                # Vẽ một đường thẳng đỏ lên ảnh gốc để đánh dấu vị trí tìm được
                cv2.line(background_img, (x, 0), (x, height), (0, 0, 255), 2)
                cv2.imwrite(os.path.join(output_dir, "step3_result.png"), background_img)
                print("Saved: step3_result.png with the detected edge.")

                return x
        
        print("Could not find any vertical edge matching the threshold.")
        return None

    except Exception as e:
        print(f"An error occurred during image processing: {e}")
        return None

# --- PHẦN CHÍNH ĐỂ CHẠY TEST ---
if __name__ == "__main__":
    image_to_test = "bg.png" # Đảm bảo file này có trong cùng thư mục
    
    # Bạn có thể điều chỉnh ngưỡng ở đây nếu cần
    # Dựa trên chiều cao 148px, ngưỡng 60 là một khởi đầu tốt (khoảng 40% chiều cao)
    pixel_threshold = 30

    print("--- Starting Captcha Solver Test ---")
    x_position = find_puzzle_gap_x_coordinate(image_to_test, pixel_threshold)

    if x_position is not None:
        print(f"\n✅ SUCCESS: The calculated drag distance is: {x_position} pixels")
    else:
        print(f"\n❌ FAILED: Could not determine the drag distance.")

    print("\nCheck the 'debug_images' folder to see the processing steps.")