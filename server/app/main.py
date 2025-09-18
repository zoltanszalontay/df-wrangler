from fastapi import FastAPI
import hydra
from omegaconf import OmegaConf
import os
from dotenv import load_dotenv # Import load_dotenv

# Function to create and configure the FastAPI app
def create_fastapi_app() -> FastAPI:
    load_dotenv() # Load environment variables from .env file
    # Initialize Hydra programmatically
    # The path is relative to the current file (app/main.py)
    with hydra.initialize(config_path="conf", version_base=None):
        cfg = hydra.compose(config_name="config")

    # Pass the loaded config to services that need it
    from app.services.llm_service import LLMService
    llm_service_instance = LLMService(config=cfg)

    # Import endpoints after llm_service_instance is created
    from app.api import endpoints

    fastapi_app = FastAPI()

    # Pass the llm_service_instance to the endpoints router
    endpoints.router.llm_service = llm_service_instance
    fastapi_app.include_router(endpoints.router)

    return fastapi_app

# Create the FastAPI app instance at the top level
app = create_fastapi_app()

# Optional: Add a root endpoint for basic checks
@app.get("/")
def read_root():
    return {"message": "Welcome to the Dataframe Wrangler API"}

# The following block is for running with `python app/main.py`
# It's not needed if you run with `uvicorn app.main:app`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)