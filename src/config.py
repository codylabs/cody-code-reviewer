import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')