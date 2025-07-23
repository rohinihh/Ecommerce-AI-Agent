#!/usr/bin/env python3
"""
Simple runner script for VS Code
Just run: python run.py
"""

import os
from app import app, init_database

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Check API key
    if not os.environ.get('GEMINI_API_KEY'):
        print("⚠️  Set GEMINI_API_KEY in .env file for AI features")
    
    print("🚀 E-commerce AI Agent starting...")
    print("🌐 Open: http://localhost:5000")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)