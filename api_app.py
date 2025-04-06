from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from recommendation_model import recommend_assessments  # make sure this function returns a pandas DataFrame
import pandas as pd
import numpy as np

app = FastAPI()

# Request body model
class QueryRequest(BaseModel):
    text: str

# POST endpoint for recommendation
@app.post("/recommend/")
async def recommend_assessments_api(request: QueryRequest):
    try:
        # Get recommendations as a pandas DataFrame
        results = recommend_assessments(request.text)

        # Replace problematic float values for JSON serialization
        results.replace([np.inf, -np.inf], np.nan, inplace=True)
        results = results.where(pd.notnull(results), None)

        # Convert DataFrame to JSON-serializable format
        response_data = results.to_dict(orient='records')

        return JSONResponse(content={"recommendations": response_data})

    except Exception as e:
        # Catch any error and return a 500
        return JSONResponse(content={"error": str(e)}, status_code=500)
