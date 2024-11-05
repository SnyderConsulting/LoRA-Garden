from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
import threading
import json
import os
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Add CORS middleware to allow requests from the frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict origins appropriately
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CIVITAI_API_URL = "https://civitai.com/api/v1/models"
CIVITAI_API_KEY = os.getenv('CIVITAI_API_KEY')
GARDEN_FILE = 'garden.json'
file_lock = threading.Lock()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def civitai_get(url, params=None):
    headers = {}
    if CIVITAI_API_KEY:
        headers['Authorization'] = f'Bearer {CIVITAI_API_KEY}'
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)  # Increased timeout
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from Civitai API: {e}")
        raise HTTPException(status_code=502, detail="Error fetching data from external API")

# Data Models
class LoRAModel(BaseModel):
    id: int
    name: str
    creatorName: str
    imageUrl: Optional[str] = None
    modelVersions: Optional[List]

class Container(BaseModel):
    name: str
    loRAs: List[int] = []

class Garden(BaseModel):
    containers: List[Container] = []

# Utility functions for data persistence
def load_garden_data() -> Garden:
    with file_lock:
        if not os.path.exists(GARDEN_FILE):
            # Create an empty garden if the file doesn't exist
            garden = Garden()
            with open(GARDEN_FILE, 'w') as f:
                json.dump(garden.dict(), f)
            return garden
        else:
            with open(GARDEN_FILE, 'r') as f:
                data = json.load(f)
                garden = Garden(**data)
                return garden

def save_garden_data(garden: Garden):
    with file_lock:
        with open(GARDEN_FILE, 'w') as f:
            json.dump(garden.dict(), f, indent=4)

# Endpoint to get the garden data
@app.get("/garden", response_model=Garden)
def get_garden():
    return load_garden_data()

# Endpoint to add a new container
class ContainerCreateRequest(BaseModel):
    name: str

@app.post("/garden/containers")
def create_container(container_request: ContainerCreateRequest):
    garden = load_garden_data()
    # Check if container already exists
    if any(c.name == container_request.name for c in garden.containers):
        raise HTTPException(status_code=400, detail="Container already exists")
    container = Container(name=container_request.name)
    garden.containers.append(container)
    save_garden_data(garden)
    return {"message": "Container added", "container": container}

# Endpoint to add a LoRA to a container
class AddLoRARequest(BaseModel):
    container_name: str
    lora_id: int

@app.post("/garden/containers/add-lora")
def add_lora_to_container(add_lora_request: AddLoRARequest):
    garden = load_garden_data()
    container = next((c for c in garden.containers if c.name == add_lora_request.container_name), None)
    if container is None:
        raise HTTPException(status_code=404, detail="Container not found")
    if add_lora_request.lora_id not in container.loRAs:
        container.loRAs.append(add_lora_request.lora_id)
        save_garden_data(garden)
    return {"message": "LoRA added to container", "container": container}

# Endpoint to remove a LoRA from a container
class RemoveLoRARequest(BaseModel):
    container_name: str
    lora_id: int

@app.post("/garden/containers/remove-lora")
def remove_lora_from_container(remove_lora_request: RemoveLoRARequest):
    garden = load_garden_data()
    container = next((c for c in garden.containers if c.name == remove_lora_request.container_name), None)
    if container is None:
        raise HTTPException(status_code=404, detail="Container not found")
    if remove_lora_request.lora_id in container.loRAs:
        container.loRAs.remove(remove_lora_request.lora_id)
        save_garden_data(garden)
    return {"message": "LoRA removed from container", "container": container}

# Endpoint to delete a container
class DeleteContainerRequest(BaseModel):
    container_name: str

@app.delete("/garden/containers")
def delete_container(delete_container_request: DeleteContainerRequest):
    garden = load_garden_data()
    container_index = next((i for i, c in enumerate(garden.containers) if c.name == delete_container_request.container_name), None)
    if container_index is None:
        raise HTTPException(status_code=404, detail="Container not found")
    del garden.containers[container_index]
    save_garden_data(garden)
    return {"message": "Container deleted"}

# Endpoint to get a model by ID (needed for displaying LoRAs in the garden)
@app.get("/models/{model_id}")
def get_model(model_id: int):
    logger.info(f"Received request for model ID: {model_id}")

    # Fetch model data
    try:
        response = civitai_get(f"https://civitai.com/api/v1/models/{model_id}")
        response.raise_for_status()
        model_data = response.json()
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Fetch images for the model using /images endpoint
    try:
        images_response = civitai_get("https://civitai.com/api/v1/images", params={"modelId": model_id})
        images_response.raise_for_status()
        images_data = images_response.json()
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching images for model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Filter images to only include those with a prompt in 'meta'
    images = []
    for image in images_data.get("items", []):
        meta = image.get("meta") or {}
        if meta.get("prompt"):
            images.append({
                "id": image["id"],
                "url": image["url"],
                "nsfw": image.get("nsfw", False),
                "width": image.get("width"),
                "height": image.get("height"),
                "meta": meta
            })

    # Collect trained words from modelVersions
    trained_words_set = set()
    for version in model_data.get("modelVersions", []):
        trained_words = version.get("trainedWords", [])
        trained_words_set.update(trained_words)

    model = {
        "id": model_data["id"],
        "name": model_data["name"],
        "description": model_data.get("description", ""),
        "creatorName": model_data.get("creator", {}).get("username", "Unknown"),
        "trainedWords": list(trained_words_set),
        "images": images
    }

    return model

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

    response = civitai_get(CIVITAI_API_URL, params=params)
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
