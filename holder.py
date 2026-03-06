import os
import requests

API_KEY = os.getenv("TYPHOON_API_KEY")

if not API_KEY:
    raise ValueError("Typhoon API key not found in environment variables")