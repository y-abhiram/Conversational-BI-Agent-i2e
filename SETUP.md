# Setup Guide - Conversational BI Agent

Complete step-by-step setup instructions for local development.

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **~2GB free RAM** (for in-memory database)
- **~1GB disk space** (for dataset)

## Quick Start (5 minutes)

```bash
# 1. Clone or download the project
cd i2c

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Download dataset
python download_data.py
# Follow the instructions to download from Kaggle

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Start backend (in one terminal)
python main.py

# 6. Frontend setup (in another terminal)
cd ../frontend
npm install
npm run dev

# 7. Open browser
# Visit: http://localhost:3000
```

Done! You should see the Conversational BI interface.

---

## Detailed Setup Instructions

### Step 1: Backend Setup

#### 1.1 Create Virtual Environment

```bash
cd backend
python -m venv venv
```

#### 1.2 Activate Virtual Environment

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

#### 1.3 Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (API framework)
- DuckDB (analytics database)
- LangChain + OpenAI (LLM integration)
- Pandas (data processing)
- Pydantic (validation)

### Step 2: Download Dataset

#### Option A: Automatic (with Kaggle API)

```bash
# Install Kaggle CLI
pip install kaggle

# Configure Kaggle credentials
# Get your API key from: https://www.kaggle.com/settings
# Place kaggle.json in ~/.kaggle/ (Linux/Mac) or C:\Users\<username>\.kaggle\ (Windows)

# Download dataset
python download_data.py
```

#### Option B: Manual Download

1. Go to [Kaggle Dataset](https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis)
2. Click "Download" (requires free Kaggle account)
3. Extract ZIP file
4. Copy these files to `backend/data/`:
   - orders.csv
   - order_products__prior.csv
   - order_products__train.csv
   - products.csv
   - aisles.csv
   - departments.csv

#### Verify Data

```bash
python download_data.py
```

Should output: "All required files are present!"

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or use any text editor
```

**Required configuration:**

```env
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.1
```

**Optional configuration:**

```env
DATA_DIR=./data
DUCKDB_PATH=./data/instacart.duckdb  # Leave empty for in-memory
HOST=0.0.0.0
PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:3000
```

### Step 4: Start Backend Server

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Loading dataset...
INFO:     Loaded tables: {'orders': 3421083, 'order_products_prior': 32434489, ...}
INFO:     Conversational BI Agent ready!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test the API:**

Visit: http://localhost:8000/docs

You should see FastAPI's auto-generated documentation.

### Step 5: Frontend Setup

Open a **new terminal** (keep backend running).

```bash
cd frontend
npm install
```

This installs:
- Next.js 14 (React framework)
- Recharts (charting library)
- TailwindCSS (styling)
- TypeScript (type safety)

### Step 6: Start Frontend

```bash
npm run dev
```

You should see:
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### Step 7: Open Application

Visit: **http://localhost:3000**

You should see the Conversational BI interface with example queries.

---

## Testing the System

### Basic Functionality Test

1. **Try an example query:**
   - Click: "What are the top 10 most ordered products?"
   - Should see results in ~2-5 seconds
   - Should display a bar chart

2. **Try a custom query:**
   - Type: "Show me orders by hour of day"
   - Should generate a line chart

3. **Test conversational memory:**
   - Ask: "Which department has the most orders?"
   - Then ask: "Show me the top 5 products in that department"
   - Should understand context from previous question

### Run Automated Tests

```bash
cd backend

# Run test suite
python test_queries.py
```

Expected output:
```
TEST SUMMARY
================================================================================
Total: 15
Passed: 14
Failed: 1
Success Rate: 93.3%
```

(Some complex queries may fail depending on LLM variability)

### Performance Benchmark

Query the large table:

```
"Count total items in all orders"
```

Expected performance:
- **First run:** ~5-10 seconds (loading data)
- **Subsequent runs:** ~1-2 seconds (DuckDB caching)
- **Result:** Should handle 32M+ rows without issues

---

## Troubleshooting

### Backend Issues

#### Error: "OPENAI_API_KEY not found"

```bash
# Make sure .env file exists and has your key
cat backend/.env

# Should show:
OPENAI_API_KEY=sk-...
```

#### Error: "CSV file not found"

```bash
# Verify data files
ls backend/data/

# Should show:
orders.csv
order_products__prior.csv
...

# If missing, re-run download script
python backend/download_data.py
```

#### Error: "Module not found"

```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

#### Port 8000 already in use

```bash
# Change port in .env
PORT=8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9  # Linux/Mac
```

### Frontend Issues

#### Error: "Cannot connect to backend"

1. Verify backend is running on http://localhost:8000
2. Check CORS settings in backend/.env
3. Try accessing http://localhost:8000/health directly

#### Port 3000 already in use

```bash
# Next.js will automatically try 3001, 3002, etc.
# Or specify port manually:
PORT=3001 npm run dev
```

#### Blank page / JavaScript errors

```bash
# Clear Next.js cache
rm -rf frontend/.next
npm run dev
```

### Dataset Issues

#### "Memory error" when loading data

**Symptoms:** System crashes or slows down significantly

**Solution:** Use persistent DuckDB instead of in-memory

```env
# In backend/.env
DUCKDB_PATH=./data/instacart.duckdb
```

This trades a bit of speed for much lower RAM usage.

#### Slow query performance

**For development:**

Use a data subset by modifying the load:

```python
# In backend/database/duckdb_manager.py, modify load_data():
self.conn.execute(f"""
    CREATE TABLE {table_name} AS
    SELECT * FROM read_csv_auto('{csv_path}')
    LIMIT 100000  -- Sample only
""")
```

---

## Development Tips

### Hot Reload

Both backend and frontend support hot reload:

- **Backend:** Automatically reloads on Python file changes
- **Frontend:** Automatically reloads on TypeScript/CSS changes

Just edit files and save!

### API Documentation

FastAPI provides interactive docs:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Database Inspection

```python
# Start Python REPL in backend directory
python

from database.duckdb_manager import DuckDBManager

db = DuckDBManager(data_dir="./data")
db.connect()
db.load_data()

# Run custom queries
result = db.execute_query("SELECT COUNT(*) FROM orders")
print(result)
```

### Monitoring Costs

OpenAI API costs depend on usage:

- **GPT-4 Turbo:** ~$0.01 per query (varies by complexity)
- **Average query:** ~2,000 tokens input + 500 tokens output
- **Estimated cost for 100 queries:** ~$1.50

To minimize costs during development:

```env
# Use GPT-3.5 (10x cheaper but less accurate)
OPENAI_MODEL=gpt-3.5-turbo
```

---

## Next Steps

Once setup is complete:

1. **Read the [README.md](README.md)** for architecture details
2. **Try the example queries** to understand capabilities
3. **Explore the code** to see implementation patterns
4. **Customize the system** for your needs

### Customization Ideas

- Add new visualizations (e.g., heatmaps, multi-line charts)
- Implement query caching with Redis
- Add export to Excel/PDF
- Create scheduled reports
- Add authentication/authorization
- Deploy to production (see DEPLOYMENT.md - coming soon)

---

## Getting Help

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Review error messages in terminal
3. Check API logs at http://localhost:8000/docs
4. Verify environment variables are set correctly
5. Ensure dataset is downloaded completely

## System Requirements

**Minimum:**
- 4GB RAM
- 2 CPU cores
- 2GB disk space

**Recommended:**
- 8GB RAM (for full 32M row dataset)
- 4+ CPU cores
- 5GB disk space
- SSD for faster data loading

---

**Setup complete!** You now have a production-grade Conversational BI Agent running locally.
