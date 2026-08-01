import os
import logging
from dotenv import load_dotenv


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "dummy_groq_key")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "dummy_tavily_key")

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging():
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
