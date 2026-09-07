from pathlib import Path

Base_dir = Path(__file__).resolve().parent
MEMORY = Base_dir / "memory.json"

MODEL = "ornith-1.5:9b"

CONTEXT_LENGTH = 4096

OLLAMA_OPTIONS = {
    "num_ctx": CONTEXT_LENGTH,
    "num_batch": 512,
    "num_thread": 6,
}


ART = """
█   █  ███  █     █     █████   
█░  █░█ ░░█ █░    █░    █░░░░░  
█░█ █░█████░█░░   █░░   ████░░░ 
██░██░█░░░█░█░░   █░░   █░░░░   
█░░ █░█░░░█░█████ █████ █████░  
 ░░░ ░░░░  ░░░░░░░ ░░░░░ ░░░░░  
  ░   ░ ░   ░ ░░░░░ ░░░░░ ░░░░░ 
"""
