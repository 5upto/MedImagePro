import os
import sys
import tkinter as tk

# Add project root directory to sys.path to resolve imports correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import Dicomet

def main():
    root = tk.Tk()
    app = Dicomet(root)
    root.mainloop()

if __name__ == "__main__":
    main()
