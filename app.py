import streamlit as st
import pandas as pd
import numpy as np
import os
import gdown
import zipfile
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="SHL Assessment Recommender", layout="wide")

# ---------------------------
# Download model from Google Drive if not present
# ---------------------------
@st.cache_resource
def load_model():
    MODEL_DIR = "all-MiniLM-L6-v2"
    FILE_ID = "1TlFk7WRL0vNNWVOTq8BpQmxwuaBTjJt7"  # ✅ your correct ID
    ZIP_FILE = "model.zip"

    if not os.path.exists(MODEL_DIR):
        st.info("📥 Downloading model from Google Drive...")
        gdown.download(f"https://drive.google.com/uc?id={FILE_ID}", ZIP_FILE, quiet=False)
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(".")
        os.remove(ZIP_FILE)

    return SentenceTransformer(MODEL_DIR)

# ---------------------------
# Load local data files
# ---------------------------
@st.cache_data
def load_data():
    df = pd.read_csv('shl_assessments_data.csv')
    embeddings = np.load('corpus_embeddings.npy')
    return df, embeddings

model = load_model()
df, corpus_embeddings = load_data()

# ---------------------------
# Recommend assessments
# ---------------------------
def recommend_assessments(user_input, top_n=10):
    query_embedding = model.encode([user_input])
    similarity_scores = cosine_similarity(query_embedding, corpus_embeddings)[0]
    top_indices = similarity_scores.argsort()[::-1][:top_n]

    results = df.loc[top_indices, [
        'Assessment Name', 'URL', 'Remote Testing', 'Adaptive/IRT', 'Duration', 'Test Type'
    ]].copy()

    results['Assessment Name'] = results.apply(
        lambda row: f"[{row['Assessment Name']}]({row['URL']})", axis=1
    )

    return results.drop(columns='URL').reset_index(drop=True)

# ---------------------------
# Extract text from job URL
# ---------------------------
def extract_text_from_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)[:1500]
    except Exception as e:
        return f"Error while fetching URL: {str(e)}"

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🔍 SHL Assessment Recommender")

st.markdown("Enter a **natural language query** or **job description URL** (e.g., from LinkedIn), and get SHL assessment recommendations.")

user_input = st.text_area("📝 Enter your query or job description URL", height=200)

if st.button("Recommend Assessments"):
    if not user_input.strip():
        st.warning("Please enter a query or job URL.")
    else:
        with st.spinner("Fetching recommendations..."):
            if user_input.startswith("http"):
                extracted_text = extract_text_from_url(user_input)
                st.subheader("🔎 Extracted Job Description Text")
                st.write(extracted_text)
                user_input = extracted_text

            results = recommend_assessments(user_input)

        if results.empty:
            st.error("No suitable assessments found.")
        else:
            st.subheader("📋 Top Assessment Recommendations")
            st.markdown(results.to_markdown(index=False), unsafe_allow_html=True)

st.markdown("---")
st.caption("Built with ❤️ by Sarthak Aggarwal")
