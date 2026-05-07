
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
    #Uses spacy to extract keywords from description to better pre-process the data 
    _nlp, _, _ = get_resources()
    doc = _nlp(text)
    return [t.lemma_.lower() for t in doc if t.pos_ in ["NOUN", "ADJ"] and not t.is_stop]

# --- MATH FUNCTIONS --- #CHECK IF PYTHON HAS A LIBRARY FOR THIS 

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

def match_lost_found(lost_report, found_report):
    """
    Main matching logic for UWI Lost and Found.
    Handles Vision-to-Vision, Text-to-Text, and Cross-Modal (Text-to-Vision) matching.
    """
    # 1. Category Setup
    lost_cat = lost_report.description.item_type
    found_cat = found_report.description.item_type
    
    # Quick exit for type mismatch (e.g., Electronics vs. Books)
    if lost_cat != found_cat:
        return {
            "final_score": 0.0, 
            "is_high_match": False,
            "match_status": "none",
            "image_score": 0,
            "text_score": 0,
            "keyword_score": 0,
            "lost_category": lost_cat,
            "found_category": found_cat,
            "category_match": False
        }

    # 2. Text Pre-processing
    l_text = lost_report.description.text_description or ""
    f_text = found_report.description.text_description or ""
    
    # Clean up placeholder text so it doesn't skew AI results
    if f_text.lower() == "no description":
        f_text = "" 

    # 3. Component Scoring
    # Keyword Score (spaCy)
    l_keys = extract_keyword(l_text)
    f_keys = extract_keyword(f_text)
    kw_score = keyword_similarity(l_keys, f_keys)

    # Text Similarity Score (CLIP Text-to-Text)
    text_score = 0
    if lost_report.description.text_embedding and found_report.description.text_embedding and f_text != "":
        text_score = cosine_similarity(
            lost_report.description.text_embedding, 
            found_report.description.text_embedding
        )

    # Image Score (CLIP Vision-to-Vision OR Cross-Modal)
    img_score = 0
    l_img_vec = getattr(lost_report.description, 'image_embedding', None)
    f_img_vec = getattr(found_report.description, 'image_embedding', None)
    l_text_vec = lost_report.description.text_embedding

    if l_img_vec and f_img_vec:
        # Scenario A: Both have images
        img_score = cosine_similarity(l_img_vec, f_img_vec)
    elif l_text_vec and f_img_vec:
        # Scenario B: Lost has text, Found has image (Cross-Modal)
        img_score = cosine_similarity(l_text_vec, f_img_vec)

    # 4. Final Score Calculation & Dynamic Thresholding
    # Path 1: Found Item has no usable text description
    if not f_text:
        final_score = img_score
        if l_img_vec and f_img_vec:
            high_threshold = 0.65
            potential_threshold = 0.50
        else:
            # Cross-modal thresholds (lower due to different vector spaces)
            high_threshold = 0.35
            potential_threshold = 0.28
    
    # Path 2: Both have full data (Text + Image)
    elif img_score > 0 and text_score > 0:
        final_score = (0.6 * img_score) + (0.3 * text_score) + (0.1 * kw_score)
        high_threshold = 0.60
        potential_threshold = 0.45
    
    # Path 3: Fallback (Text-to-Text only)
    else:
        final_score = (0.8 * text_score) + (0.2 * kw_score)
        high_threshold = 0.55
        potential_threshold = 0.40

    # 5. Determine Match Status
    match_status = "none"
    if final_score >= high_threshold:
        match_status = "high"
    elif final_score >= potential_threshold:
        match_status = "potential"

    return {
        "final_score": round(final_score, 4),
        "match_status": match_status,
        "is_high_match": match_status == "high",
        "threshold_used": high_threshold,
        "image_score": round(img_score, 4),
        "text_score": round(text_score, 4),
        "keyword_score": round(kw_score, 4),
        "lost_category": lost_cat,
        "found_category": found_cat,
        "category_match": True
    }