# Quick Start Guide - 10 Minutes to Running

Get the Conversational BI Agent running in 10 minutes.

---

## Prerequisites Check

Before starting, verify you have:

```bash
# Python 3.11+
python --version
# Should show: Python 3.11.x or higher

# Node.js 18+
node --version
# Should show: v18.x.x or higher

# npm
npm --version
# Should show: 9.x.x or higher
```

Don't have these? [Full setup instructions](SETUP.md)

---

## Step 1: Download Dataset (3 minutes)

The dataset is available from Kaggle. You have two options:

### Option A: Automatic Download (recommended if you have Kaggle API)

```bash
cd backend
pip install kaggle

# Get Kaggle API credentials:
# 1. Go to https://www.kaggle.com/settings
# 2. Click "Create New API Token"
# 3. Place kaggle.json in ~/.kaggle/ (Linux/Mac) or C:\Users\<username>\.kaggle\ (Windows)

python download_data.py
```

### Option B: Manual Download

1. Go to https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis
2. Click "Download" (requires free Kaggle account - takes 1 minute to create)
3. Extract the ZIP file
4. Copy these 6 files to `backend/data/`:
   - `orders.csv`
   - `order_products__prior.csv`
   - `order_products__train.csv`
   - `products.csv`
   - `aisles.csv`
   - `departments.csv`

**Verify download:**

```bash
cd backend
python download_data.py
# Should show: "All required files are present!"
```

---

## Step 2: Backend Setup (3 minutes)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies (takes ~2 minutes)
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use any text editor
```

**In `.env`, set:**

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Get OpenAI API key:**
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy and paste into `.env`

---

## Step 3: Start Backend (1 minute)

```bash
# Make sure you're in backend/ directory with venv activated
python main.py
```

**Expected output:**

```
INFO:     Started server process
INFO:     Loading dataset...
INFO:     Loaded tables: {'orders': 3421083, 'order_products_prior': 32434489, ...}
INFO:     Conversational BI Agent ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**✅ Backend is running!**

Test it: Open http://localhost:8000/health in your browser

**Keep this terminal open** (backend must stay running)

---

## Step 4: Frontend Setup (2 minutes)

**Open a NEW terminal** (keep backend running in the first one)

```bash
cd frontend

# Install dependencies (takes ~1-2 minutes)
npm install

# Start development server
npm run dev
```

**Expected output:**

```
ready - started server on 0.0.0.0:3000
```

**✅ Frontend is running!**

---

## Step 5: Open Application (30 seconds)

Open your browser to:

**http://localhost:3000**

You should see the Conversational BI interface!

---

## Step 6: Try Your First Query (1 minute)

Click on one of the example queries, or type:

**"What are the top 10 most ordered products?"**

You should see:
1. "Thinking..." status
2. "Executing query..." status
3. Results with a bar chart
4. Execution time (~2-5 seconds)

**🎉 Success! You're now running the Conversational BI Agent!**

---

## Quick Test - Try These Queries

**Simple aggregation:**
```
How many total orders are there?
```

**Multi-table join:**
```
Which department has the most orders?
```

**Time-series:**
```
Show me orders by hour of day
```

**Complex query:**
```
Which aisles have the highest reorder rate?
```

**Conversational follow-up:**
```
First: "Which department has the most orders?"
Then: "Show me the top 5 products in that department"
```

---

## Troubleshooting

### "Module not found" error

```bash
# Make sure virtual environment is activated
which python  # Should point to venv/bin/python

# If not, activate it:
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### "OPENAI_API_KEY not found"

```bash
# Check .env file exists and has your key
cat backend/.env

# Should show:
OPENAI_API_KEY=sk-...
```

### "Cannot connect to backend"

1. Verify backend is running: http://localhost:8000/health
2. Check for errors in backend terminal
3. Make sure port 8000 isn't blocked

### "CSV file not found"

```bash
# Verify data files exist
ls backend/data/

# Should show all 6 CSV files
# If missing, re-run Step 1 (download dataset)
```

### Port already in use

**Backend (port 8000):**
```bash
# Change port in backend/.env
PORT=8001

# Restart backend
python main.py
```

**Frontend (port 3000):**
```bash
# Next.js will automatically try 3001, 3002, etc.
# Or specify manually:
PORT=3001 npm run dev
```

### Slow performance / Out of memory

If you have less than 4GB RAM available:

```bash
# Edit backend/.env
DUCKDB_PATH=./data/instacart.duckdb

# This uses persistent storage instead of in-memory
# Slightly slower but much lower RAM usage
```

---

## What to Do Next

Now that it's running:

1. **Explore the UI** - Try different types of questions
2. **View the SQL** - Click "View SQL & Reasoning" to see generated queries
3. **Check the API docs** - Visit http://localhost:8000/docs
4. **Read the architecture** - See [ARCHITECTURE.md](ARCHITECTURE.md)
5. **Run tests** - Try `python backend/test_queries.py`

---

## Development Tips

### Hot Reload

Both backend and frontend auto-reload when you edit files:

- **Backend:** Edit Python files → saves automatically reload
- **Frontend:** Edit TypeScript/CSS → browser auto-refreshes

### Viewing Logs

**Backend logs:**
Check the terminal where you ran `python main.py`

**Frontend logs:**
Check browser console (F12 → Console tab)

### Stopping the Servers

**Backend:**
Press `Ctrl+C` in the backend terminal

**Frontend:**
Press `Ctrl+C` in the frontend terminal

### Restarting

```bash
# Backend
cd backend
source venv/bin/activate
python main.py

# Frontend (in new terminal)
cd frontend
npm run dev
```

---

## Cost Estimate

With OpenAI API:

- **Per query:** ~$0.01 (GPT-4 Turbo)
- **10 queries:** ~$0.10
- **100 queries:** ~$1.00

**To reduce costs during testing:**

Edit `backend/.env`:
```env
OPENAI_MODEL=gpt-3.5-turbo  # 10x cheaper, but less accurate
```

---

## System Requirements

**Minimum:**
- 4GB RAM
- 2 CPU cores
- 2GB free disk space
- Internet connection (for OpenAI API)

**Recommended:**
- 8GB RAM (for full dataset in memory)
- 4+ CPU cores
- SSD for faster data loading

---

## Next Steps

✅ **You're up and running!**

**To learn more:**
- [README.md](README.md) - Project overview
- [SETUP.md](SETUP.md) - Detailed setup instructions
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and trade-offs
- [PRESENTATION.md](PRESENTATION.md) - How to demo this project

**To customize:**
- Add new example queries
- Modify chart types
- Adjust LLM temperature
- Add new visualization types

---

## Getting Help

If you encounter issues:

1. Check [Troubleshooting](#troubleshooting) above
2. Review error messages in terminals
3. Verify all prerequisites are installed
4. Check that dataset downloaded completely

---

**🎉 Congratulations! You now have a production-grade Conversational BI Agent running locally.**

**Total time: ~10 minutes**

Enjoy exploring the system! 🚀
