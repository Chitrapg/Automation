import os
import certifi
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env if present
load_dotenv()

# Ensure certificates are set (required for HTTPS on some systems)
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

# ========== CONFIG ==========
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")  # e.g. "https://your-domain.atlassian.net/wiki"
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")  # your Atlassian email
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")  # your Atlassian API token
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")  # e.g. "OLMS"

# Vision model from Groq docs (supports text+image)
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Optional: if you want to create pages under a specific parent page
PARENT_PAGE_ID = os.getenv("CONFLUENCE_PARENT_PAGE_ID")  # can be None


def get_groq_client() -> Groq:
    """Return a configured Groq client instance."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set in environment.")
    return Groq(api_key=GROQ_API_KEY)


def validate_confluence_config() -> None:
    """Validate that required Confluence configuration is present."""
    if not all([CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, CONFLUENCE_BASE_URL, CONFLUENCE_SPACE_KEY]):
        raise RuntimeError(
            "Confluence config (CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, "
            "CONFLUENCE_BASE_URL, CONFLUENCE_SPACE_KEY) is missing or incomplete."
        )
