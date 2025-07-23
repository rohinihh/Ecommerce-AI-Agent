#!/usr/bin/env python3
"""
E-commerce AI Agent - Main Application
Simple Flask app with embedded database initialization and AI query processing
"""

import os
import json
import logging
import sqlite3
from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini AI
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Database path
DB_PATH = "ecommerce.db"

# Function definitions need to be before initialization
def init_database():
    """Initialize database with tables and sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        product_id TEXT UNIQUE,
        product_name TEXT,
        category TEXT,
        brand TEXT,
        price REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS total_sales_metrics (
        id INTEGER PRIMARY KEY,
        product_id TEXT,
        total_sales REAL,
        units_sold INTEGER,
        revenue REAL,
        date TEXT,
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ad_sales_metrics (
        id INTEGER PRIMARY KEY,
        product_id TEXT,
        ad_spend REAL,
        ad_sales REAL,
        clicks INTEGER,
        impressions INTEGER,
        cpc REAL,
        date TEXT,
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    """)
    
    # Check if data exists
    cursor.execute("SELECT COUNT(*) FROM total_sales_metrics")
    if cursor.fetchone()[0] == 0:
        load_excel_data(cursor)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def load_excel_data(cursor):
    """Load data from Excel files"""
    try:
        records_loaded = 0
        
        # Load Total Sales data
        sales_file = "data/Product-Level Total Sales and Metrics (mapped).xlsx"
        if os.path.exists(sales_file):
            df_sales = pd.read_excel(sales_file)
            logger.info(f"Found sales file with {len(df_sales)} rows, columns: {list(df_sales.columns)}")
            
            # Direct mapping for your Excel files
            actual_cols = {
                'Product ID': 'item_id',
                'Total Sales': 'total_sales', 
                'Units Sold': 'total_units_ordered',
                'Revenue': 'total_sales',  # Using total_sales as revenue
                'Date': 'date'
            }
            
            logger.info(f"Mapped columns: {actual_cols}")
            
            for _, row in df_sales.iterrows():
                try:
                    cursor.execute("""
                    INSERT INTO total_sales_metrics 
                    (product_id, total_sales, units_sold, revenue, date) 
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(row.get(actual_cols.get('Product ID', ''), '')),
                        float(row.get(actual_cols.get('Total Sales', ''), 0)) if pd.notna(row.get(actual_cols.get('Total Sales', ''))) else 0,
                        int(row.get(actual_cols.get('Units Sold', ''), 0)) if pd.notna(row.get(actual_cols.get('Units Sold', ''))) else 0,
                        float(row.get(actual_cols.get('Revenue', ''), 0)) if pd.notna(row.get(actual_cols.get('Revenue', ''))) else 0,
                        str(row.get(actual_cols.get('Date', ''), '2024-01-01'))
                    ))
                    records_loaded += 1
                except Exception as e:
                    logger.warning(f"Error inserting sales row: {e}")
                    continue
        
        # Load Ad Sales data  
        ads_file = "data/Product-Level Ad Sales and Metrics (mapped).xlsx"
        if os.path.exists(ads_file):
            df_ads = pd.read_excel(ads_file)
            logger.info(f"Found ads file with {len(df_ads)} rows")
            
            # Direct mapping for ad sales data
            actual_ad_cols = {
                'Product ID': 'item_id',
                'Ad Spend': 'ad_spend',
                'Ad Sales': 'ad_sales', 
                'Clicks': 'clicks',
                'Impressions': 'impressions',
                'CPC': 'ad_spend'  # Will calculate CPC as ad_spend/clicks
            }
            
            for _, row in df_ads.iterrows():
                try:
                    cursor.execute("""
                    INSERT INTO ad_sales_metrics 
                    (product_id, ad_spend, ad_sales, clicks, impressions, cpc, date) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get(actual_ad_cols.get('Product ID', ''), '')),
                        float(row.get(actual_ad_cols.get('Ad Spend', ''), 0)) if pd.notna(row.get(actual_ad_cols.get('Ad Spend', ''))) else 0,
                        float(row.get(actual_ad_cols.get('Ad Sales', ''), 0)) if pd.notna(row.get(actual_ad_cols.get('Ad Sales', ''))) else 0,
                        int(row.get(actual_ad_cols.get('Clicks', ''), 0)) if pd.notna(row.get(actual_ad_cols.get('Clicks', ''))) else 0,
                        int(row.get(actual_ad_cols.get('Impressions', ''), 0)) if pd.notna(row.get(actual_ad_cols.get('Impressions', ''))) else 0,
                        (row.get('ad_spend', 0) / row.get('clicks', 1)) if row.get('clicks', 0) > 0 else 0,
                        '2024-01-01'
                    ))
                    records_loaded += 1
                except Exception as e:
                    logger.warning(f"Error inserting ad row: {e}")
                    continue
        
        # Load Product data
        products_file = "data/Product-Level Eligibility Table (mapped).xlsx"
        if os.path.exists(products_file):
            df_products = pd.read_excel(products_file)
            logger.info(f"Found products file with {len(df_products)} rows")
            
            for _, row in df_products.iterrows():
                try:
                    # Map eligibility data to products
                    cursor.execute("""
                    INSERT OR IGNORE INTO products 
                    (product_id, product_name, category, brand, price) 
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(row.get('item_id', '')),
                        f"Product {row.get('item_id', '')}",
                        'General',
                        'Unknown',
                        0
                    ))
                    records_loaded += 1
                except Exception as e:
                    logger.warning(f"Error inserting product row: {e}")
                    continue
        
        logger.info(f"Successfully loaded {records_loaded} records from Excel files")
        
        if records_loaded == 0:
            raise Exception("No records were loaded from Excel files")
        
    except Exception as e:
        logger.error(f"Error loading Excel data: {e}")
        raise Exception(f"Excel data loading failed: {str(e)}")

# Initialize database on startup
logger.info("Initializing database...")
init_database()

def init_database():
    """Initialize database with tables and sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        product_id TEXT UNIQUE,
        product_name TEXT,
        category TEXT,
        brand TEXT,
        price REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS total_sales_metrics (
        id INTEGER PRIMARY KEY,
        product_id TEXT,
        total_sales REAL,
        units_sold INTEGER,
        revenue REAL,
        date TEXT,
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ad_sales_metrics (
        id INTEGER PRIMARY KEY,
        product_id TEXT,
        ad_spend REAL,
        ad_sales REAL,
        clicks INTEGER,
        impressions INTEGER,
        cpc REAL,
        date TEXT,
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    """)
    
    # Check if data exists
    cursor.execute("SELECT COUNT(*) FROM total_sales_metrics")
    if cursor.fetchone()[0] == 0:
        load_excel_data(cursor)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def load_excel_data(cursor):
    """Load data from Excel files"""
    try:
        records_loaded = 0
        
        # Load Total Sales data
        sales_file = "data/Product-Level Total Sales and Metrics (mapped)_1753162181292.xlsx"
        if os.path.exists(sales_file):
            df_sales = pd.read_excel(sales_file)
            logger.info(f"Found sales file with {len(df_sales)} rows, columns: {list(df_sales.columns)}")
            
            # Direct mapping for your Excel files
            actual_cols = {
                'Product ID': 'item_id',
                'Total Sales': 'total_sales', 
                'Units Sold': 'total_units_ordered',
                'Revenue': 'total_sales',  # Using total_sales as revenue
                'Date': 'date'
            }
            
            logger.info(f"Mapped columns: {actual_cols}")
            
            for _, row in df_sales.iterrows():
                try:
                    cursor.execute("""
                    INSERT INTO total_sales_metrics 
                    (product_id, total_sales, units_sold, revenue, date) 
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(row.get(actual_cols.get('Product ID', ''), '')),
                        float(row.get(actual_cols.get('Total Sales', ''), 0)) if pd.notna(row.get(actual_cols.get('Total Sales', ''))) else 0,
                        int(row.get(actual_cols.get('Units Sold', ''), 0)) if pd.notna(row.get(actual_cols.get('Units Sold', ''))) else 0,
                        float(row.get(actual_cols.get('Revenue', ''), 0)) if pd.notna(row.get(actual_cols.get('Revenue', ''))) else 0,
                        str(row.get(actual_cols.get('Date', ''), '2024-01-01'))
                    ))
                    records_loaded += 1
                except Exception as e:
                    logger.warning(f"Error inserting sales row: {e}")
                    continue
        
        # Load Ad Sales data  
        ads_file = "data/Product-Level Ad Sales and Metrics (mapped)_1753162181290.xlsx"
        if os.path.exists(ads_file):
            df_ads = pd.read_excel(ads_file)
            logger.info(f"Found ads file with {len(df_ads)} rows")
            
            # Direct mapping for ad sales data
            actual_ad_cols = {
                'Product ID': 'item_id',
                'Ad Spend': 'ad_spend',
                'Ad Sales': 'ad_sales', 
                'Clicks': 'clicks',
                'Impressions': 'impressions',
                'CPC': 'ad_spend'  # Will calculate CPC as ad_spend/clicks
            }
            
            for _, row in df_ads.iterrows():
                try:
                    cursor.execute("""
                    INSERT INTO ad_sales_metrics 
                    (product_id, ad_spend, ad_sales, clicks, impressions, cpc, date) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get(actual_ad_cols.get('Product ID', ''), '')),
                        float(row.get(actual_ad_cols.get('Ad Spend', ''), 0)) if pd.notna(row.get(actual_ad_cols.get('Ad Spend', ''))) else 0,
                        float(row.get(actual_ad_cols.get('Ad Sales', ''), 0)) if pd.notna(row.get(actual_ad_cols.get('Ad Sales', ''))) else 0,
                        int(row.get(actual_ad_cols.get('Clicks', ''), 0)) if pd.notna(row.get(actual_ad_cols.get('Clicks', ''))) else 0,
                        int(row.get(actual_ad_cols.get('Impressions', ''), 0)) if pd.notna(row.get(actual_ad_cols.get('Impressions', ''))) else 0,
                        (row.get('ad_spend', 0) / row.get('clicks', 1)) if row.get('clicks', 0) > 0 else 0,
                        '2024-01-01'
                    ))
                    records_loaded += 1
                except Exception as e:
                    logger.warning(f"Error inserting ad row: {e}")
                    continue
        
        # Load Product data
        products_file = "data/Product-Level Eligibility Table (mapped)_1753162181291.xlsx"
        if os.path.exists(products_file):
            df_products = pd.read_excel(products_file)
            logger.info(f"Found products file with {len(df_products)} rows")
            
            for _, row in df_products.iterrows():
                try:
                    # Map eligibility data to products
                    cursor.execute("""
                    INSERT OR IGNORE INTO products 
                    (product_id, product_name, category, brand, price) 
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(row.get('item_id', '')),
                        f"Product {row.get('item_id', '')}",
                        'General',
                        'Unknown',
                        0
                    ))
                    records_loaded += 1
                except Exception as e:
                    logger.warning(f"Error inserting product row: {e}")
                    continue
        
        logger.info(f"Successfully loaded {records_loaded} records from Excel files")
        
        if records_loaded == 0:
            raise Exception("No records were loaded from Excel files")
        
    except Exception as e:
        logger.error(f"Error loading Excel data: {e}")
        raise Exception(f"Excel data loading failed: {str(e)}")

def get_database_schema():
    """Get database schema information for AI context"""
    return """
    Database Schema:
    
    1. products: product_id, product_name, category, brand, price
    2. total_sales_metrics: product_id, total_sales, units_sold, revenue, date
    3. ad_sales_metrics: product_id, ad_spend, ad_sales, clicks, impressions, cpc, date
    
    Sample queries:
    - Total sales: SELECT SUM(total_sales) FROM total_sales_metrics
    - RoAS calculation: SELECT ad_sales/ad_spend AS roas FROM ad_sales_metrics
    """

def convert_question_to_sql(question):
    """Convert natural language question to SQL using Gemini AI"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        You are a SQL expert. Convert this question to a valid SQLite query.
        
        {get_database_schema()}
        
        Question: {question}
        
        Return only a JSON object with:
        {{"sql": "your SQL query", "explanation": "brief explanation"}}
        
        Rules:
        - Use proper SQLite syntax
        - For total sales, use SUM(total_sales) FROM total_sales_metrics
        - For RoAS, use ad_sales/ad_spend
        - Return valid JSON only
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON from response
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        return json.loads(response_text)
        
    except Exception as e:
        logger.error(f"Error converting question: {e}")
        # Fallback for common questions
        if "total sales" in question.lower():
            return {
                "sql": "SELECT SUM(total_sales) AS total_sales FROM total_sales_metrics",
                "explanation": "Calculate total sales from all records"
            }
        return {"sql": None, "explanation": f"Error: {str(e)}"}

def execute_sql_query(sql):
    """Execute SQL query and return results"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        conn.close()
        return results
        
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        return []

def format_response(question, results, sql_info):
    """Format the results into a human-readable response"""
    if not results:
        return "No data found for your question."
    
    try:
        # Use AI to format the response
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        Format this data into a clear answer. Remove currency symbols.
        
        Question: {question}
        SQL: {sql_info.get('sql', '')}
        Results: {results}
        
        Provide a clear, concise answer with numbers formatted with commas.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        # Simple fallback formatting
        if len(results) == 1 and len(results[0]) == 1:
            value = list(results[0].values())[0]
            if isinstance(value, (int, float)):
                return f"The result is {value:,.2f}"
        return f"Found {len(results)} results: {results}"

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-commerce AI Agent</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        .chat-container { max-height: 400px; overflow-y: auto; }
        .loading { display: none; }
    </style>
</head>
<body>
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8 mx-auto">
                <h1 class="text-center mb-4">E-commerce AI Agent</h1>
                
                <div class="card">
                    <div class="card-body">
                        <div class="chat-container mb-3" id="chatContainer">
                            <div class="alert alert-info">
                                Ask me about your e-commerce data! Try:
                                <ul class="mb-0">
                                    <li>"What is my total sales?"</li>
                                    <li>"Calculate the RoAS"</li>
                                    <li>"Show me revenue by date"</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="input-group">
                            <input type="text" class="form-control" id="questionInput" 
                                   placeholder="Ask your question..." onkeypress="handleKeyPress(event)">
                            <button class="btn btn-primary" onclick="askQuestion()">Ask</button>
                        </div>
                        
                        <div class="loading text-center mt-3" id="loading">
                            <div class="spinner-border text-primary"></div>
                            <p>Processing your question...</p>
                        </div>
                    </div>
                </div>
                
                <div class="mt-3 text-muted text-center">
                    <small>Database: {{ stats.total_records }} records loaded</small>
                </div>
            </div>
        </div>
    </div>

    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                askQuestion();
            }
        }

        async function askQuestion() {
            const input = document.getElementById('questionInput');
            const question = input.value.trim();
            
            if (!question) return;
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            
            // Add user question to chat
            addMessage('You: ' + question, 'alert-secondary');
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage('AI: ' + data.formatted_response, 'alert-success');
                    if (data.sql_query) {
                        addMessage('SQL: ' + data.sql_query, 'alert-info small');
                    }
                } else {
                    addMessage('Error: ' + (data.error || 'Unknown error'), 'alert-danger');
                }
                
            } catch (error) {
                addMessage('Error: Failed to process question', 'alert-danger');
            }
            
            // Hide loading and clear input
            document.getElementById('loading').style.display = 'none';
            input.value = '';
        }

        function addMessage(message, className) {
            const container = document.getElementById('chatContainer');
            const div = document.createElement('div');
            div.className = 'alert ' + className + ' mb-2';
            div.textContent = message;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM total_sales_metrics")
    total_records = cursor.fetchone()[0]
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, stats={'total_records': total_records})

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Process natural language questions"""
    try:
        data = request.json
        question = data.get('question', '')
        
        if not question:
            return jsonify({'success': False, 'error': 'No question provided'})
        
        logger.info(f"Processing question: {question}")
        
        # Handle common questions directly to avoid AI API issues
        if "total sales" in question.lower():
            results = execute_sql_query("SELECT SUM(total_sales) AS total_sales FROM total_sales_metrics")
            if results:
                total = results[0]['total_sales']
                return jsonify({
                    'success': True,
                    'question': question,
                    'sql_query': 'SELECT SUM(total_sales) AS total_sales FROM total_sales_metrics',
                    'explanation': 'Calculate total sales from all records',
                    'results': results,
                    'formatted_response': f"Your total sales are {total:,.2f} from {len(results)} records loaded from Excel files."
                })
        
        elif "roas" in question.lower() or "return on ad spend" in question.lower():
            results = execute_sql_query("SELECT AVG(ad_sales / ad_spend) AS avg_roas FROM ad_sales_metrics WHERE ad_spend > 0")
            if results:
                roas = results[0]['avg_roas']
                return jsonify({
                    'success': True,
                    'question': question,
                    'sql_query': 'SELECT AVG(ad_sales / ad_spend) AS avg_roas FROM ad_sales_metrics WHERE ad_spend > 0',
                    'explanation': 'Calculate average Return on Ad Spend',
                    'results': results,
                    'formatted_response': f"Your average RoAS is {roas:.2f}"
                })
        
        elif "records" in question.lower() or "data" in question.lower():
            sales_count = execute_sql_query("SELECT COUNT(*) AS count FROM total_sales_metrics")[0]['count']
            ad_count = execute_sql_query("SELECT COUNT(*) AS count FROM ad_sales_metrics")[0]['count']
            return jsonify({
                'success': True,
                'question': question,
                'sql_query': 'Database record counts',
                'explanation': 'Show loaded data statistics',
                'results': [{'sales_records': sales_count, 'ad_records': ad_count}],
                'formatted_response': f"Loaded {sales_count} sales records and {ad_count} ad records from your Excel files."
            })
        
        # For other questions, try AI (with fallback)
        try:
            sql_info = convert_question_to_sql(question)
            
            if not sql_info.get('sql'):
                return jsonify({
                    'success': False, 
                    'error': sql_info.get('explanation', 'Could not generate SQL')
                })
            
            results = execute_sql_query(sql_info['sql'])
            formatted_response = format_response(question, results, sql_info)
            
            return jsonify({
                'success': True,
                'question': question,
                'sql_query': sql_info['sql'],
                'explanation': sql_info.get('explanation', ''),
                'results': results,
                'formatted_response': formatted_response
            })
            
        except Exception as ai_error:
            logger.warning(f"AI processing failed: {ai_error}, trying direct SQL")
            return jsonify({
                'success': False,
                'error': f"AI service temporarily unavailable. Try asking 'total sales', 'RoAS', or 'records' for now."
            })
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Check for API key
    if not os.environ.get('GEMINI_API_KEY'):
        print("⚠️  WARNING: GEMINI_API_KEY not found!")
        print("Set it in your environment or .env file")
    
    print("🚀 Starting E-commerce AI Agent...")
    print("🌐 Web interface: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)