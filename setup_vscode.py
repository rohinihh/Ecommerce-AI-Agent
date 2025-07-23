#!/usr/bin/env python3
"""
One-click VS Code setup script
Run this to install all dependencies and set up your environment
"""

import subprocess
import sys
import os

def install_packages():
    """Install required packages"""
    packages = [
        "flask>=2.3.0",
        "google-generativeai>=0.3.0", 
        "python-dotenv>=1.0.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0"
    ]
    
    print("📦 Installing packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed: {package}")
            return False
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""# E-commerce AI Agent Environment
GEMINI_API_KEY=your_api_key_here
FLASK_ENV=development
FLASK_DEBUG=1
""")
        print("📝 Created .env file - add your GEMINI_API_KEY")
    else:
        print("✅ .env file already exists")

def main():
    print("🚀 Setting up E-commerce AI Agent for VS Code...")
    print("-" * 50)
    
    # Install packages
    if not install_packages():
        print("❌ Package installation failed")
        return
    
    # Create environment file
    create_env_file()
    
    print("-" * 50)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your GEMINI_API_KEY")
    print("2. Run: python run.py")
    print("3. Open: http://localhost:5000")
    print("\nFor VS Code debugging: Press F5")

if __name__ == "__main__":
    main()