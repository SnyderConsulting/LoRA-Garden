from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Add CORS middleware to allow requests from the frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production to restrict origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CIVITAI_API_URL = "https://civitai.com/api/v1/models"

@app.get("/models")
def search_models(
    query: str = Query(None, description="Search query to filter models by name"),
    limit: int = Query(10, description="The number of results to be returned per page"),
    page: int = Query(1, description="The page number to return"),
):
    params = {
        "limit": limit,
        "page": page,
        "types": "LORA",
    }

    if query:
        params["query"] = query

    response = requests.get(CIVITAI_API_URL, params=params)
    response.raise_for_status()
    data = response.json()

    # Simplify the data to only include what we need
    models = []
    for item in data.get("items", []):
        model = {
            "id": item["id"],
            "name": item["name"],
            "creatorName": item.get("creator", {}).get("username", "Unknown"),
            "modelVersions": item.get("modelVersions", []),
        }
        # Get the first image URL from the model versions
        if model["modelVersions"]:
            images = model["modelVersions"][0].get("images", [])
            if images:
                model["imageUrl"] = images[0]["url"]
            else:
                model["imageUrl"] = None
        else:
            model["imageUrl"] = None

        models.append(model)

    return {"models": models}
