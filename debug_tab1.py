import sys
import main
sys.argv = [
    'main.py',       # Giả lập tên script,
    "tab2",            # Giả lập tham số 1
    "TVGS 25BDCF-TM,3401208233,C25TNL,121,560800,7570800",   # Giả lập tham số 2
]

try:
    main.main()
except SystemExit as e:
    # Bắt lỗi SystemExit để script debug không bị đóng đột ngột khi updater gọi sys.exit()
    print(f"\nUpdater exited with code: {e.code}")
except Exception as e:
    print(f"\nAn uncaught exception occurred in updater: {e}")

print("\n--- DEBUG SCRIPT FINISHED ---") 