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

from sentence_transformers import SentenceTransformer, CrossEncoder

# Initialize model once
_model = None
_cross_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model
    
def get_cross_model():
    global _cross_model
    if _cross_model is None:
        _cross_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return _cross_model

def embed(text):
    """Generate a vector embedding for the given text using sentence-transformers."""
    model = get_model()
    # Handle single string
    if isinstance(text, str):
        return model.encode(text).tolist()
    # Handle batch of strings
    return model.encode(text).tolist()

def cross_score(query, texts):
    """Compute cross-encoder relevance scores for a query against a list of texts."""
    if not texts:
        return []
    cross_model = get_cross_model()
    pairs = [(query, text) for text in texts]
    scores = cross_model.predict(pairs)
    return scores.tolist()