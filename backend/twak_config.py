import os
from dotenv import load_dotenv

load_dotenv()

TWAK_AGENT_ADDRESS = os.getenv("TWAK_AGENT_ADDRESS")

def get_twak_status():
    return {
        "status": "configured" if TWAK_AGENT_ADDRESS else "missing",
        "agent_address": TWAK_AGENT_ADDRESS,
        "chain": "BSC",
        "registration": "ready" if TWAK_AGENT_ADDRESS else "not_ready"
    }