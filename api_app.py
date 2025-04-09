from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Load model and data
model = SentenceTransformer('./all-MiniLM-L6-v2') 
df = pd.read_csv('shl_assessments_data.csv')
corpus_embeddings = np.load('corpus_embeddings.npy')

class QueryRequest(BaseModel):
    text: str

# Health check route
@app.get("/health")
def health_check():
    return {"status": "ok"}

def recommend_assessments(user_input, top_n=10):
    query_embedding = model.encode([user_input])
    similarity_scores = cosine_similarity(query_embedding, corpus_embeddings)[0]
    top_indices = similarity_scores.argsort()[::-1][:top_n]

    results = df.loc[top_indices, [
        'Assessment Name', 'URL', 'Remote Testing', 'Adaptive/IRT', 'Duration', 'Test Type'
    ]].copy()

    return results.reset_index(drop=True)


# POST API
@app.post("/recommend/")
async def recommend_assessments_api(request: QueryRequest):
    try:
        results = recommend_assessments(request.text)
        results.replace([np.inf, -np.inf], np.nan, inplace=True)
        results = results.where(pd.notnull(results), None)
        return JSONResponse(content={"recommendations": results.to_dict(orient='records')})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/recommend/", response_class=HTMLResponse)
async def get_textbox():
    html_content = """
    <html>
        <head>
            <title>SHL Assessment Recommender</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f4f6f8;
                }
                .container {
                    text-align: center;
                    background: white;
                    padding: 2rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }
                input[type="text"] {
                    width: 400px;
                    padding: 10px;
                    font-size: 1rem;
                    margin-top: 1rem;
                }
                button {
                    padding: 10px 16px;
                    font-size: 1rem;
                    margin-left: 10px;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 style="color: #2c3e50;">SHL Assessment Recommender</h1>
                <p style="font-size: 1.1rem;">Enter your query or Job URL:</p>
                <form action="/recommend/form/" method="post">
                    <input type="text" name="text" required />
                    <button type="submit">Recommend</button>
                </form>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Handle form submission
@app.post("/recommend/form", response_class=JSONResponse)
async def handle_form_json(text: str = Form(...)):
    try:
        results = recommend_assessments(text)
        results.replace([np.inf, -np.inf], np.nan, inplace=True)
        results = results.where(pd.notnull(results), None)
        return JSONResponse(content={"input": text, "recommendations": results.to_dict(orient='records')})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
