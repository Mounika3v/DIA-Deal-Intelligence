from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    hindsight_api_key: str = os.getenv("HINDSIGHT_API_KEY", "")
    hindsight_api_url: str = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")
    hindsight_bank_id: str = os.getenv("HINDSIGHT_BANK_ID", "dia-sales-memory")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

settings = Settings()
