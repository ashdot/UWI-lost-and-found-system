# import os
# import spacy
# import clip
# import torch
# import requests
# from io import BytesIO
# from PIL import Image

# # 1. Setup Device
# device = "cuda" if torch.cuda.is_available() else "cpu"

# # 2. Load spaCy (The Keyword Expert)
# try:
#     nlp = spacy.load("en_core_web_sm")
# except OSError:
#     # Fallback in case the model isn't linked correctly
#     import spacy.cli
#     spacy.cli.download("en_core_web_sm")
#     nlp = spacy.load("en_core_web_sm")

# # 3. Load CLIP (The Visual/Semantic Brain)
# base_dir = os.path.dirname(os.path.abspath(__file__))
# model_path = os.path.join(base_dir, "ViT-B-32.pt")

# if os.path.exists(model_path):
#     # Load from your local file (prevents URLError/Internet checks)
#     model, preprocess = clip.load(model_path, device=device)
#     print(f"✅ CLIP loaded locally from: {model_path}")
# else:
#     # Fallback to internet download if file is missing
#     print("⚠️ Local model not found. Attempting to download...")
#     model, preprocess = clip.load("ViT-B/32", device=device)

# # 4. Set to Evaluation Mode (Important for consistency)
# model.eval()

# #Extracts Keyword using SpAcy 
# def extract_keyword(text):
#     doc = nlp(text)

#     keywords = [
#         token.lemma_.lower()
#         for token in doc
#         if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop
#     ]

#     return keywords


# #IMAGE ENCODING 
# def encode_image(image_url): 
#     response = requests.get(image_url) #Gets URL from Cloundinary 
#     image = Image.open(BytesIO(response.content)).convert("RGB")
    
#     image = preprocess(image).unsqueeze(0).to(device)

#     with torch.no_grad(): 
#         image_features = model.encode_image(image)

#     return image_features


# # TEXT ENCODING
# def encode_text(text):

#     text_token = clip.tokenize([text]).to(device)

#     with torch.no_grad(): #Used to save computation
#         text_features = model.encode_text(text_token)

#     return text_features


# # SIMILARITY
# def cosine_similarity(img_feat, text_feat):

#     img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
#     text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)

#     return (img_feat @ text_feat.T).item()

# #KEY WORD SIMILARITY 
# def keyword_similarity(lost_keywords, found_keywords):
#     if not lost_keywords or not found_keywords:
#         return 0.0

#     lost_set = set(lost_keywords)
#     found_set = set(found_keywords)

#     intersection = lost_set.intersection(found_set)

#     return len(intersection) / len(lost_set.union(found_set))

# #Matching Algorithim 
# def match_lost_found(lost_report, found_report):
#     """
#     lost_report: An instance of LostItemReport
#     found_report: An instance of FoundItemReport
#     """
#     lost_desc = lost_report.description
#     found_desc = found_report.description

#     # Different types no matching 
#     if lost_desc.item_type != found_desc.item_type:
#         return {"final_score": 0.0, "is_high_match": False}

#     # No embeddings no matching 
#     if not lost_desc.text_embedding or not found_desc.text_embedding:
#         return {"final_score": 0.0, "is_high_match": False}
    
#     # KEYWORD SIMILARITY (spaCy)
#     lost_keywords = extract_keyword(lost_desc.text_description)
#     found_keywords = extract_keyword(found_desc.text_description)
#     keyword_score = keyword_similarity(lost_keywords, found_keywords)

#     # SIMILARITY
#     # Converts saved PickleType (lists) back to PyTorch Tensors

#     # Use .unsqueeze(0) to ensure the dimensions match  @ T math
#     lost_text_vec = torch.tensor(lost_desc.text_embedding).to(device).unsqueeze(0)
#     found_text_vec = torch.tensor(found_desc.text_embedding).to(device).unsqueeze(0)
#     text_score = cosine_similarity(lost_text_vec, found_text_vec)

#     # 4. IMAGE SIMILARITY 
#     image_score = 0
#     # Checks if both items actually have saved image embeddings
#     if hasattr(lost_desc, 'image_embedding') and lost_desc.image_embedding and \
#        hasattr(found_desc, 'image_embedding') and found_desc.image_embedding:
        
#         lost_img_vec = torch.tensor(lost_desc.image_embedding).to(device)
#         found_img_vec = torch.tensor(found_desc.image_embedding).to(device)
#         image_score = cosine_similarity(lost_img_vec, found_img_vec)
    
#     # FINAL WEIGHTED CALCULATION
#     if image_score > 0:
#         # Image 60% Text 30% Keywords 10%
#         final_score = (0.6 * image_score) + (0.3 * text_score) + (0.1 * keyword_score)
#     else:
#         # If no image, Text and Keywords are used
#         final_score = (0.8 * text_score) + (0.2 * keyword_score)


#     return {
#         "final_score": round(final_score, 4),
#         "image_score": round(image_score, 4),
#         "text_score": round(text_score, 4),
#         "keyword_score": round(keyword_score, 4),
#         "is_high_match": final_score > 0.8
#     }

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
            # We moved the import to the top, so just call it here
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

    # 1. Keyword Score
    l_keys = extract_keyword(lost_report.description.text_description)
    f_keys = extract_keyword(found_report.description.text_description)
    kw_score = keyword_similarity(l_keys, f_keys)

    # 2. Text Score
    text_score = 0
    if lost_report.description.text_embedding and found_report.description.text_embedding:
        text_score = cosine_similarity(
            lost_report.description.text_embedding, 
            found_report.description.text_embedding
        )

    # 3. Image Score
    img_score = 0
    if hasattr(lost_report.description, 'image_embedding') and lost_report.description.image_embedding:
        if hasattr(found_report.description, 'image_embedding') and found_report.description.image_embedding:
            img_score = cosine_similarity(
                lost_report.description.image_embedding,
                found_report.description.image_embedding
            )

    # 4. Final Calculation
    if img_score > 0:
        final_score = (0.6 * img_score) + (0.3 * text_score) + (0.1 * kw_score)
    else:
        final_score = (0.8 * text_score) + (0.2 * kw_score)

    return {
        "final_score": round(final_score, 4),
        "is_high_match": final_score > 0.75 # Adjusted threshold slightly
    }