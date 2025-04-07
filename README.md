# SHL Assessment Recommendation System

An end-to-end project to build a smart SHL Assessment Recommendation System. It scrapes SHL's official product catalog, processes the data using NLP techniques, and provides assessment recommendations based on job descriptions or queries. The system includes both a Streamlit web interface and a FastAPI backend.

---

## 🚀 Project Overview

This project consists of 3 major components:

1. **Web Scraping**  
2. **Recommendation Model**  
3. **Web App + API Deployment**

---

## 1️⃣ Web Scraping

**Goal:** Extract structured data from the SHL assessment catalog (type=1 and type=2).

**Libraries Used:**
- `Selenium`
- `BeautifulSoup`
- `asyncio`, `ThreadPoolExecutor`
- `pandas`, `numpy`

**Scraped Fields:**
- Assessment Name  
- Assessment URL  
- Remote Testing Support  
- Adaptive/IRT Support  
- Duration  
- Test Type  
- Job Description  
- Job Levels  
- Languages  

**Output File:**  
`shl_assessments_data.csv`

---

## 2️⃣ Recommendation Model

**Goal:** Recommend top SHL assessments based on user query or job description.

**Libraries Used:**
- `SentenceTransformers` (`all-MiniLM-L6-v2`)
- `scikit-learn` (cosine similarity)
- `NumPy`, `Pandas`

**Workflow:**
- Embed assessment descriptions using SBERT
- Encode user query/job description
- Compute cosine similarity between input and all embeddings
- Return top 10 recommended assessments

**Features:**
- Accepts raw text or job description URL (auto-text extraction)
- Returns top relevant SHL assessments

---

## 3️⃣ Web Interface & API

### 🌐 Streamlit Web App
- Simple UI for user input
- Shows extracted job description (if URL provided)
- Displays top 10 recommendations in a table

### ⚙️ FastAPI Backend
- Endpoint: `POST /recommend/`
- Input: JSON with text or URL
- Output: Top recommendations as JSON

---

## 📂 Repository Structure

```bash
.
├── webscrap_data.py             # Script to scrape SHL catalog
├── shl_assessments_data.csv     # Scraped assessment dataset
├── corpus_embeddings.npy        # Precomputed sentence embeddings
├── recommendation_model.py      # Model logic and similarity functions
├── app.py                       # Streamlit frontend
├── api_app.py                   # FastAPI backend
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
