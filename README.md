# LoRA Garden

LoRA Garden is a web application that allows users to search for LoRA models, organize them into personalized containers (gardens), and generate optimized prompts using selected models and user input. The application integrates with the [Civitai API](https://civitai.com/) to fetch model data and with the [OpenAI API](https://openai.com/api/) to generate prompts.

## Features

- **Search LoRA Models**: Find LoRA models using the Civitai API.
- **Organize Models**: Add models to containers within your garden for easy management.
- **Generate Prompts**: Create customized prompts based on selected models and your own input.
- **View Model Details**: Access detailed information and images for each model.

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/CXD3GD8mBR4/0.jpg)](https://www.youtube.com/watch?v=CXD3GD8mBR4)

## Repository Structure

- `/backend`: Contains the Python FastAPI backend application.
- `/frontend`: Contains the React frontend application.

## Prerequisites

- **Python 3.8+** for the backend.
- **Node.js v12+ and npm** for the frontend.
- **OpenAI API Key**: Required for prompt generation.
- **Civitai API Key** (optional): For increased API rate limits.

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/yourusername/loragarden.git
cd loragarden
```

### Backend Setup

1. **Navigate to the backend directory:**

   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**

   - Copy the example environment file and rename it to `.env`:

     ```bash
     cp .env_example .env
     ```

   - Open the `.env` file and add your API keys:

     ```ini
     CIVITAI_API_KEY=your_civitai_api_key
     OPENAI_API_KEY=your_openai_api_key
     ```

     - `CIVITAI_API_KEY` is optional but recommended for higher rate limits.
     - `OPENAI_API_KEY` is **required** for generating prompts.

5. **Run the Backend Server:**

   ```bash
   uvicorn main:app --reload
   ```

   The backend API will be accessible at `http://localhost:8000`.

### Frontend Setup

1. **Navigate to the frontend directory:**

   ```bash
   cd ../frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Start the Frontend Application:**

   ```bash
   npm start
   ```

   The frontend will be accessible at `http://localhost:3000`.

### Access the Application

Open your web browser and navigate to `http://localhost:3000` to start using LoRA Garden.

## Usage Guide

### Searching for Models

- Use the search bar on the main page to find LoRA models.
- Browse through the search results and view model details.

### Managing Your Garden

- Navigate to the "My Garden" page to view your containers.
- Create new containers to organize your favorite models.
- Add models to containers directly from the search results.

### Generating Prompts

- Within a container, select images and input your own prompt.
- Click "Generate" to create an optimized prompt that leverages the selected models.
- View and copy the generated prompt for your use.

## API Endpoints

### Backend (FastAPI)

- **`GET /models`**: Search for LoRA models.
- **`GET /models/{model_id}`**: Retrieve details for a specific model.
- **`GET /garden`**: Get the current state of your garden.
- **`POST /garden/containers`**: Create a new container.
- **`POST /garden/containers/add-lora`**: Add a LoRA model to a container.
- **`POST /garden/containers/remove-lora`**: Remove a LoRA model from a container.
- **`DELETE /garden/containers`**: Delete a container.
- **`POST /generate`**: Generate a prompt based on selected models and user input.

## Configuration Details

### Environment Variables (`backend/.env`)

- **`CIVITAI_API_KEY`**: Your Civitai API key (optional).
- **`OPENAI_API_KEY`**: Your OpenAI API key (required).

### Notes

- Ensure that the backend is running on `http://localhost:8000` and the frontend is set up to communicate with it.
- If you face rate limiting with the Civitai API, consider providing your API key in the `.env` file.

## Dependencies

### Backend Requirements (`backend/requirements.txt`)

- **FastAPI**: Web framework for building APIs with Python.
- **Uvicorn**: ASGI server implementation for Python.
- **Requests**: HTTP library for Python.
- **Pydantic**: Data validation library for Python.
- **Tenacity**: Library for retrying code.
- **OpenAI**: Official OpenAI API client.

### Frontend Dependencies (`frontend/package.json`)

- **React**: JavaScript library for building user interfaces.
- **Chakra UI**: Component library for React.
- **Axios**: Promise-based HTTP client for the browser and Node.js.
- **React Router Dom**: DOM bindings for React Router.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss changes or enhancements.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- **[Civitai](https://civitai.com/)** for providing the LoRA models API.
- **[OpenAI](https://openai.com/)** for the language model used in prompt generation.
