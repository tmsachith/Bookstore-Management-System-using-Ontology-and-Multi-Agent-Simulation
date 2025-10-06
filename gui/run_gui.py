import sys
import os

# Add the parent directory to Python path for importing bookstore_system
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the GUI
from bookstore_gui import main

if __name__ == "__main__":
    print("Starting TM Sachith's Bookstore Management System...")
    print("Interface loading...")
    main()
