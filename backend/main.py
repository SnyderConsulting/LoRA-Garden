from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import threading
import json
import os
from typing import List, Optional

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
GARDEN_FILE = 'garden.json'
file_lock = threading.Lock()

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

# Existing endpoints...

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
    response = requests.get(f"https://civitai.com/api/v1/models/{model_id}")
    if response.status_code == 200:
        data = response.json()
        model = {
            "id": data["id"],
            "name": data["name"],
            "creatorName": data.get("creator", {}).get("username", "Unknown"),
            "modelVersions": data.get("modelVersions", []),
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

        return model
    else:
        raise HTTPException(status_code=response.status_code, detail="Model not found")

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
