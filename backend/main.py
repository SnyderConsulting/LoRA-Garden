from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
import threading
import json
import os
from openai import OpenAI
import re
from typing import List, Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
# openai.api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI()

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
        response = requests.get(url, params=params, headers=headers, timeout=10)  # Increased timeout
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
    description: Optional[str] = None
    trainedWords: Optional[List[str]] = []
    selectedImagePrompts: List[str] = []

class Container(BaseModel):
    name: str
    loRAs: List[int] = []
    modelDetails: Dict[str, LoRAModel] = {}  # Cache model details

class Garden(BaseModel):
    containers: List[Container] = []

class GenerateRequest(BaseModel):
    modelsData: List[LoRAModel]
    userPrompt: str

# Endpoint to delete a container
class DeleteContainerRequest(BaseModel):
    container_name: str

# Endpoint to add a new container
class ContainerCreateRequest(BaseModel):
    name: str

# Endpoint to add a LoRA to a container
class AddLoRARequest(BaseModel):
    container_name: str
    lora_id: int

# Endpoint to remove a LoRA from a container
class RemoveLoRARequest(BaseModel):
    container_name: str
    lora_id: int

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

@app.post("/garden/containers/add-lora")
def add_lora_to_container(add_lora_request: AddLoRARequest):
    garden = load_garden_data()
    container = next((c for c in garden.containers if c.name == add_lora_request.container_name), None)
    if container is None:
        raise HTTPException(status_code=404, detail="Container not found")
        
    if add_lora_request.lora_id not in container.loRAs:
        container.loRAs.append(add_lora_request.lora_id)
        
        # Fetch and store model details if not already cached
        if str(add_lora_request.lora_id) not in container.modelDetails:
            try:
                response = civitai_get(f"https://civitai.com/api/v1/models/{add_lora_request.lora_id}")
                model_data = response.json()
                
                # Get first image URL from model versions if available
                image_url = None
                if model_data.get("modelVersions"):
                    images = model_data["modelVersions"][0].get("images", [])
                    if images:
                        image_url = images[0].get("url")
                
                # Collect trained words from all versions
                trained_words = []
                for version in model_data.get("modelVersions", []):
                    trained_words.extend(version.get("trainedWords", []))
                
                model_details = LoRAModel(
                    id=model_data["id"],
                    name=model_data["name"],
                    creatorName=model_data.get("creator", {}).get("username", "Unknown"),
                    imageUrl=image_url,
                    description=model_data.get("description", ""),
                    trainedWords=list(set(trained_words))
                )
                
                container.modelDetails[str(add_lora_request.lora_id)] = model_details
                
            except Exception as e:
                logger.error(f"Error fetching model details for {add_lora_request.lora_id}: {e}")
                # Continue even if we can't fetch details - we can try again later
        
        save_garden_data(garden)
    
    return {"message": "LoRA added to container", "container": container}

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

def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

@app.post("/generate")
def generate_prompt(generate_request: GenerateRequest):
    try:
        # Extract data
        models_data = generate_request.modelsData
        user_prompt = generate_request.userPrompt

        # Compose the system prompt with examples
        system_prompt = (
            "You are given data about selected LoRA models, including their descriptions, trained words, "
            "selected image prompts, and a user's prompt. Your task is to rewrite the user's prompt so that it:\n\n"
            "1. Appropriately triggers each of the selected LoRA models by including their unique trigger words "
            "and following best practices described in their descriptions.\n"
            "2. Maintains the user's original intention, enhancing it by utilizing the models' features without "
            "deviating from the intended content.\n"
            "3. Borrows from the prompt formatting found in the selected image prompts, such as length, use of tags, "
            "trigger words, and overall style.\n"
            "4. Incorporates relevant keywords, tags, or phrases that optimize the use of the selected LoRA models.\n\n"
            "Here are some examples:\n\n"
            "**Example 1:**\n"
            "Models Data:\n"
            "---\n"
            "**Model 1: Pig man**\n"
            "- **Description Highlights:** This LoRA was trained to replace males with monster pig men. No individual trigger word, but you can better activate it with **\"ugly man\"**. Also, you can use **\"multiple boys\"**. Tags to increase or modify the effect: **\"horror (theme)\", \"monster\", \"orc\", \"troll\"**.\n"
            "- **Trained Words:**\n"
            "  - **gangbang**\n"
            "  - **horror**\n"
            "  - **multiple boys**\n"
            "  - **ugly man**\n"
            "  - **monster**\n"
            "---\n"
            "**Model 2: Anime Screencap Style LoRA**\n"
            "- **Description Highlights:** Trigger keyword is **\"anime screencap\"**.\n"
            "- **Trained Words:**\n"
            "  - **anime screencap**\n"
            "- **Selected Image Prompts:**\n"
            "  1. single enchanting Island floating high into the sky. with vines hanging off of it. a tribal village resides atop it. birds fly along the outskirts of the flying island. on the ground there is a forest with a kingdom residing in it. a river running along from one corner of the landscape to the other. the island floating above has a waterfall that flows off the floating island too. hd. 4k. the sky is covered in clouds. the sun producing god rays in the sky.\n"
            "  2. a man in front of mosque building, mosque walls are red in color built with red sandstone, high tower, golden dome, epic, fog, dawn, dramatic lighting, dim light, mountain, forest, cliff, <lora:ARWMosqueOld:1> arcane style, (ghibli style)\n"
            "---\n"
            "User's Original Prompt:\n"
            "> \"A scary scene with a monster chasing a girl at night in the forest\"\n"
            "---\n"
            "Expected Rewritten Prompt:\n"
            "anime screencap, at night in a dark forest, a terrified girl is chased by an ugly man monster, horror theme, foggy atmosphere, tall trees casting eerie shadows, moonlight filtering through the leaves, dramatic lighting, tense mood, hd, 4k, epic scene\n\n"
            "**Example 2:**\n"
            "Models Data:\n"
            "---\n"
            "**Model 1: Ultimate Instagram Influencer**\n"
            "- **Description Highlights:** Activated by the trigger word **\"IG_Model\"**. Emulates influencer style, poses, fashion trends.\n"
            "- **Trained Words:**\n"
            "  - **Woman**\n"
            "  - **IG_Model**\n"
            "  - **Model**\n"
            "- **Selected Image Prompts:**\n"
            "  1. [ng_deepnegative_v1_75t:0.95] (designer wear, haute couture, luxury clothing) (designer clothing:1.2)\n"
            "     <lora:skin_slider_v10:0.5><lora:detailSliderALT2:1><lora:epiCRealismHelper:1>\n"
            "     <lora:IGInfluencer_V1:0.6> IG_Model Style-DA <lora:add_detail:-0.5>\n"
            "     <lora:HD Horizon v1_0:0.6> <lora:lyco_humans_v10:0.3> TrualityCampus_Heather\n"
            "     <lora:SDXLrender_v2.0:0.6> CS-CYBR <lora:detail_slider_v4:1>\n"
            "  2. waist up, close up, 21 year old, a beautiful, Turkish woman, IG_MODEL, sexy, posing, slight smile, (detailed skin:1.1), thicc, looking at viewer, (Platinum blonde hair:1.3), BREAK designer fashion, Purple Ribbed Knit Turtleneck Asymmetrical Hem Crop Top, BREAK (Iron-wrought bridge with cityscape backdrop:1.2), cinematic soft lighting, bokeh <lora:IGModelStyle_V1:0.8>\n"
            "---\n"
            "**Model 2: ReaLora/Realistic skin texture/**\n"
            "- **Description Highlights:** Turns art into a realistic person with skin texture. Recommendation for use: **weight 0.1 - 0.7 max**, **CFG 7+**, **Steps 24+**.\n"
            "- **Selected Image Prompts:**\n"
            "  1. [No prompt provided]\n"
            "---\n"
            "User's Original Prompt:\n"
            "> \"Beautiful influencer showing them going out downtown in a fancy city\"\n"
            "---\n"
            "Expected Rewritten Prompt:\n"
            "full body shot, 22-year-old beautiful influencer, IG_Model, stylish outfit, posing confidently, slight smile, (realistic skin texture:1.1), looking at viewer, fashionable attire, BREAK downtown in a fancy city, evening lights, (cityscape backdrop:1.2), cinematic lighting, bokeh effect <lora:ReaLora:0.6>\n\n"
            "Now, based on the above instructions and examples, please proceed with the task.\n"
        )

        # Format the models data into the specified template
        models_info = "Models Data:\n"
        for idx, model in enumerate(models_data, start=1):
            # Clean the description from HTML tags
            clean_description = remove_html_tags(model.description) if model.description else "No description available."

            models_info += "---\n"
            models_info += f"**Model {idx}: {model.name}**\n"
            models_info += f"- **Description Highlights:** {clean_description}\n"

            # Include trained words if any
            if model.trainedWords:
                models_info += "- **Trained Words:**\n"
                for word in model.trainedWords:
                    models_info += f"  - **{word}**\n"

            # Include selected image prompts if any
            if model.selectedImagePrompts:
                models_info += "- **Selected Image Prompts:**\n"
                for idx_prompt, prompt_text in enumerate(model.selectedImagePrompts, start=1):
                    models_info += f"  {idx_prompt}. {prompt_text}\n"

        # Compose the assistant prompt
        assistant_prompt = (
            f"{models_info}"
            "---\n"
            f"User's Original Prompt:\n"
            f"> \"{user_prompt}\"\n"
            "---\n"
            "Please rewrite the user's prompt according to the instructions and examples provided above."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": assistant_prompt}
        ]

        # Make the OpenAI API call
        completion = client.chat.completions.create(
            model="gpt-4o",  # Use the appropriate model available to you
            messages=messages
        )

        # Extract the assistant's response
        generated_prompt = completion.choices[0].message.content.strip()

        # Return the response to the frontend
        return {"generatedPrompt": generated_prompt}

    except Exception as e:
        logger.error(f"Error generating prompt: {e}")
        raise HTTPException(status_code=500, detail="Error generating prompt")
