from view.mainWindow import MainWindow
from PyQt5 import QtWidgets, QtCore
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
