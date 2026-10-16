import os

# Must be set before any Qt module creates a QApplication.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
