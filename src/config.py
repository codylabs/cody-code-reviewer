import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = 'gpt-5.6-luna'


def get_model() -> str:
    """Return the configured reviewer model while preserving the legacy variable."""
    return os.getenv('MODEL') or os.getenv('OPENAI_MODEL') or DEFAULT_MODEL

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
# MODEL picks the reviewer model; claude-* models use Anthropic, anything else OpenAI.
# OPENAI_MODEL is honoured for backwards compatibility with existing workflows.
MODEL = get_model()
