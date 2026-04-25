
import os
import spacy
import spacy.cli    # <--- Add this here to be safe
import clip
import torch
import requests
import numpy as np
from io import BytesIO
from PIL import Image

# Global variables initialized as None for Lazy Loading
nlp = None
model = None
preprocess = None
device = "cuda" if torch.cuda.is_available() else "cpu"


def get_resources():
    """Lazy loader for AI models. Only runs when a match is needed."""
    global nlp, model, preprocess
    
    # 1. Load spaCy
    if nlp is None:
        print("🔍 Loading spaCy...")
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

    # 2. Load CLIP
    if model is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "ViT-B-32.pt")

        if os.path.exists(model_path):
            model, preprocess = clip.load(model_path, device=device)
            print(f"✅ CLIP loaded locally from: {model_path}")
        else:
            print("⚠️ Local model not found. Downloading...")
            model, preprocess = clip.load("ViT-B/32", device=device)
        
        model.eval()
    
    return nlp, model, preprocess

# --- ENCODING FUNCTIONS ---

def generate_embeddings(text=None, image_url=None):
    """
    Called in views.py when a user SUBMITS a report.
    Generates vectors to be saved in the database.
    """
    _nlp, _model, _preprocess = get_resources()
    results = {"text_vec": None, "image_vec": None}

    if text:
        tokens = clip.tokenize([text]).to(device)
        with torch.no_grad():
            vec = _model.encode_text(tokens)
            # Convert to list for database storage (PickleType)
            results["text_vec"] = vec.cpu().numpy().tolist()[0]

    if image_url:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img_input = _preprocess(img).unsqueeze(0).to(device)
        with torch.no_grad():
            vec = _model.encode_image(img_input)
            results["image_vec"] = vec.cpu().numpy().tolist()[0]
            
    return results

def extract_keyword(text):
    _nlp, _, _ = get_resources()
    doc = _nlp(text)
    return [t.lemma_.lower() for t in doc if t.pos_ in ["NOUN", "ADJ"] and not t.is_stop]

# --- MATH FUNCTIONS (No AI models needed here) ---

def cosine_similarity(feat1, feat2):
    """Math-based similarity for vectors (tensors or lists)."""
    # Ensure inputs are tensors
    if isinstance(feat1, list): feat1 = torch.tensor(feat1).to(device)
    if isinstance(feat2, list): feat2 = torch.tensor(feat2).to(device)
    
    # Normalize
    feat1 = feat1 / feat1.norm(dim=-1, keepdim=True)
    feat2 = feat2 / feat2.norm(dim=-1, keepdim=True)

    # If 1D, make 2D for the matrix multiplication
    if feat1.ndim == 1: feat1 = feat1.unsqueeze(0)
    if feat2.ndim == 1: feat2 = feat2.unsqueeze(0)

    return (feat1 @ feat2.T).item()

def keyword_similarity(lost_keywords, found_keywords):
    if not lost_keywords or not found_keywords: return 0.0
    ls, fs = set(lost_keywords), set(found_keywords)
    return len(ls.intersection(fs)) / len(ls.union(fs))

# --- MATCHING ENGINE ---

def match_lost_found(lost_report, found_report):
    """
    Main matching logic using pre-saved embeddings.
    """
    # Quick exit for type mismatch
    if lost_report.description.item_type != found_report.description.item_type:
        return {"final_score": 0.0, "is_high_match": False}

    # Keyword Score
    l_keys = extract_keyword(lost_report.description.text_description)
    f_keys = extract_keyword(found_report.description.text_description)
    kw_score = keyword_similarity(l_keys, f_keys)

    # Text Score
    text_score = 0
    if lost_report.description.text_embedding and found_report.description.text_embedding:
        text_score = cosine_similarity(
            lost_report.description.text_embedding, 
            found_report.description.text_embedding
        )

    # Image Score
    img_score = 0
    if hasattr(lost_report.description, 'image_embedding') and lost_report.description.image_embedding:
        if hasattr(found_report.description, 'image_embedding') and found_report.description.image_embedding:
            img_score = cosine_similarity(
                lost_report.description.image_embedding,
                found_report.description.image_embedding
            )

    # Final Calculation
    # 60% for image 30% for text 10% for keyword 
    if img_score > 0:
        final_score = (0.6 * img_score) + (0.3 * text_score) + (0.1 * kw_score)
    else:
        final_score = (0.8 * text_score) + (0.2 * kw_score)

    return {
        "final_score": round(final_score, 4),
        "is_high_match": final_score > 0.60 # Made it 60 for testing 
    }

