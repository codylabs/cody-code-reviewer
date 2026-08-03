import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = 'gpt-5.6-luna'
DEFAULT_EXCLUDE_PATHS = (
    "node_modules/**,**/node_modules/**,dist/**,**/dist/**,"
    "venv/**,**/venv/**,.venv/**,**/.venv/**"
)
DEFAULT_CONTEXT_FILES = (
    "AGENTS.md,REVIEW.md,CLAUDE.md,.github/copilot-instructions.md"
)


def get_model() -> str:
    """Return the configured reviewer model while preserving the legacy variable."""
    return os.getenv('MODEL') or os.getenv('OPENAI_MODEL') or DEFAULT_MODEL


def get_csv(name: str, default: str = "") -> tuple[str, ...]:
    """Return a normalized comma-separated environment setting."""
    return tuple(
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    )


def get_exclude_paths() -> tuple[str, ...]:
    """Paths excluded from review, expressed as shell-style glob patterns."""
    return get_csv("EXCLUDE_PATHS", DEFAULT_EXCLUDE_PATHS)


def get_context_files() -> tuple[str, ...]:
    """Trusted files read from the pull request's base commit for review guidance."""
    return get_csv("CONTEXT_FILES", DEFAULT_CONTEXT_FILES)


def get_review_instructions() -> str:
    """Optional caller-supplied review priorities."""
    return os.getenv("REVIEW_INSTRUCTIONS", "").strip()


def should_update_existing_comment() -> bool:
    """Whether a new run should replace Cody's previous PR comment."""
    return os.getenv("UPDATE_EXISTING_COMMENT", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
# MODEL picks the reviewer model; claude-* models use Anthropic, anything else OpenAI.
# OPENAI_MODEL is honoured for backwards compatibility with existing workflows.
MODEL = get_model()
