from dotenv import load_dotenv
import os

load_dotenv()

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
FAL_API_KEY = os.getenv("FAL_API_KEY")
SIEVE_API_KEY = os.getenv("SIEVE_API_KEY")
