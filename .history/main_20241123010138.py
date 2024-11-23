import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
import traceback

def main():
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print("Error occurred:")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()