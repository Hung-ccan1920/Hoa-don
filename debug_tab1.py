import sys
import main
sys.argv = [
    'main.py',       # Giả lập tên script
    "TVTK 25BDCF-TA,0305094732,C25TPQ,52,3076513,41532923|TVTK 25BDCF-TU,0305094732,C25TPQ,51,3194174,43121344|TVTK 25TYCF-TR,0305094732,C25TPQ,53,2193189,29608054",        # Giả lập tham số 1
]

try:
    main.main()
except SystemExit as e:
    # Bắt lỗi SystemExit để script debug không bị đóng đột ngột khi updater gọi sys.exit()
    print(f"\nUpdater exited with code: {e.code}")
except Exception as e:
    print(f"\nAn uncaught exception occurred in updater: {e}")

print("\n--- DEBUG SCRIPT FINISHED ---")