import os
import warnings
import logging

# Suppress annoying HF and tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
warnings.filterwarnings("ignore")

import transformers
transformers.logging.set_verbosity_error()
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

from sentence_transformers import SentenceTransformer

# Initialize model once
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed(text):
    """Generate a vector embedding for the given text using sentence-transformers."""
    model = get_model()
    # Handle single string
    if isinstance(text, str):
        return model.encode(text).tolist()
    # Handle batch of strings
    return model.encode(text).tolist()