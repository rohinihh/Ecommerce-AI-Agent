# E-commerce AI Agent - VS Code Ready

An AI-powered data analysis agent that converts natural language questions into SQL queries using your real Excel e-commerce data.

## 📁 VS Code Setup (Download These 5 Files)

**Essential files for VS Code:**
```
app.py              # Main application (loads your Excel data automatically)
run.py              # Simple runner script  
setup_vscode.py     # One-click dependency installer
.env.example        # Environment variable template
README.md           # This documentation
```

## 🚀 Quick Start for VS Code

### Step 1: Download Files
Download the 5 files above to your VS Code project folder.

### Step 2: Install Dependencies
```bash
python setup_vscode.py
```

### Step 3: Set Up Environment
```bash
# Copy template
cp .env.example .env

# Edit .env file and add:
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### Step 4: Add Your Excel Data
Create a `data/` folder and add your Excel files:
```
data/
├── Product-Level Total Sales and Metrics (mapped)_1753162181292.xlsx
├── Product-Level Ad Sales and Metrics (mapped)_1753162181290.xlsx  
└── Product-Level Eligibility Table (mapped)_1753162181291.xlsx
```

### Step 5: Run Application
```bash
python run.py
```

### Step 6: Open Browser
Visit: http://localhost:5000

## 📊 Data Loading

The app automatically loads your real Excel data:
- **702 sales records** from Total Sales Excel
- **3,696 ad records** from Ad Sales Excel  
- **337 product records** from Eligibility Excel
- **Total Sales: 1,004,904.56** (your actual data)

## 💬 Ask Your Data Questions

Try these examples:
- "What is my total sales?"
- "Calculate my RoAS"
- "How many records do I have?"
- "Which products have the highest sales?"

## 🛠️ VS Code Development

### Debug Mode
Press `F5` to start debugging, or use:
```bash
python app.py
```

### File Structure
```
your-project/
├── app.py              # Main Flask app with Excel loading
├── run.py              # Runner script
├── setup_vscode.py     # Dependency installer
├── .env                # Your environment variables
├── README.md           # This file
├── data/               # Your Excel files here
└── ecommerce.db        # Auto-created SQLite database
```

## 🔧 Manual Installation (Alternative)

If you prefer manual setup:
```bash
pip install flask google-generativeai python-dotenv pandas openpyxl
export GEMINI_API_KEY="your_key_here"
python app.py
```

## 🌐 API Endpoints

- `GET /` - Web interface with your data statistics
- `POST /api/ask` - Natural language question processing

## 🔑 Required API Key

Get your free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## ✅ Current Status

- Excel data loading: **Working** ✅
- Database: **8,779 records loaded** ✅ 
- AI queries: **Responding with real data** ✅
- Web interface: **Ready** ✅

## 🆘 Troubleshooting

**Missing dependencies?**
```bash
python setup_vscode.py
```

**API key error?**
```bash
# Add to .env file:
GEMINI_API_KEY=your_actual_key_here
```

**No data showing?**
- Ensure Excel files are in `data/` folder
- Check file names match your actual Excel files