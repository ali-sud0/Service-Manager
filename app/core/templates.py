from fastapi.templating import Jinja2Templates
import os

# Get the absolute path to templates directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Create Jinja2Templates instance
templates = Jinja2Templates(directory=TEMPLATES_DIR)