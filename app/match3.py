
import os
import spacy
import spacy.cli   
import clip
import torch
import requests
import numpy as np
from io import BytesIO
from PIL import Image
import sys # SPINNER 
import threading
import time

##
# PG-VECTOR 
##


# Global variables initialized as None for Lazy Loading
nlp = None
model = None
preprocess = None
device = "cuda" if torch.cuda.is_available() else "cpu"

def spinner_task(stop_event):
    """Simple terminal spinner."""
    spin = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r⏳ Downloading AI Model... {spin[idx % 4]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write("\r✅ Download Complete!          \n")

def get_resources():
    global nlp, model, preprocess
    
    if nlp is None:
        print("🔍 Loading spaCy...")
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

    if model is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "ViT-B-32.pt")

        if os.path.exists(model_path):
            print(f"✅ CLIP loaded locally from project folder.")
            model, preprocess = clip.load(model_path, device=device)
        else:
            # 1. Start the Spinner
            stop_spinner = threading.Event()
            spinner_thread = threading.Thread(target=spinner_task, args=(stop_spinner,))
            print("⚠️ Local model not found. Waking up AI...")
            spinner_thread.start()
            
            try:
                # 2. Download/Load the model
                model, preprocess = clip.load("ViT-B/32", device=device)
                
                # 3. Save it to the project folder for next time
                torch.save(model.state_dict(), model_path)
            finally:
                # 4. Stop the spinner
                stop_spinner.set()
                spinner_thread.join()
            
            print(f"💾 Model saved to {model_path} for future offline use.")
        
        model.eval()
    
    return nlp, model, preprocess


# def get_resources():
#     global nlp, model, preprocess
    
#     if nlp is None:
#         print("🔍 Loading spaCy...")
#         try:
#             nlp = spacy.load("en_core_web_sm")
#         except OSError:
#             spacy.cli.download("en_core_web_sm")
#             nlp = spacy.load("en_core_web_sm")

#     if model is None:
#         base_dir = os.path.dirname(os.path.abspath(__file__))
#         model_path = os.path.join(base_dir, "ViT-B-32.pt")

#         if os.path.exists(model_path):
#             print(f"✅ CLIP loaded locally from: {model_path}")
#             model, preprocess = clip.load(model_path, device=device)
#         else:
#             # Start the spinner in a separate thread
#             stop_spinner = threading.Event()
#             spinner_thread = threading.Thread(target=spinner_task, args=(stop_spinner,))
            
#             print("⚠️ Local model not found. Waking up AI...")
#             spinner_thread.start()
            
#             try:
#                 # This performs the actual download/load
#                 model, preprocess = clip.load("ViT-B/32", device=device)
#             finally:
#                 # Stop the spinner regardless of success or failure
#                 stop_spinner.set()
#                 spinner_thread.join()
        
#         model.eval()
    
#     return nlp, model, preprocess
# def get_resources():
#     """Lazy loader for AI models. Only runs when a match is needed."""
#     global nlp, model, preprocess
    
#     # Loads spaCy
#     if nlp is None:
#         print("🔍 Loading spaCy...")
#         try:
#             nlp = spacy.load("en_core_web_sm")
#         except OSError:
#             spacy.cli.download("en_core_web_sm")
#             nlp = spacy.load("en_core_web_sm")

#     # Loads CLIP
#     if model is None:
#         base_dir = os.path.dirname(os.path.abspath(__file__))
#         model_path = os.path.join(base_dir, "ViT-B-32.pt")

#         if os.path.exists(model_path):
#             model, preprocess = clip.load(model_path, device=device)
#             print(f"✅ CLIP loaded locally from: {model_path}")
#         else:
#             print("⚠️ Local model not found. Downloading...")
#             model, preprocess = clip.load("ViT-B/32", device=device)

#             torch.save(model.state_dict(), model_path)
#             print(f"✅ Model saved to {model_path} for future offline use.")
        
#         model.eval()
    
#     return nlp, model, preprocess

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
            #results["text_vec"] = vec.cpu().numpy().tolist()[0]
            results["text_vec"] = vec.cpu().numpy().flatten().tolist()

    if image_url:
        response = requests.get(image_url) 
        
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img_input = _preprocess(img).unsqueeze(0).to(device)
        with torch.no_grad():
            vec = _model.encode_image(img_input)
            #results["image_vec"] = vec.cpu().numpy().tolist()[0]
            results["image_vec"] = vec.cpu().numpy().flatten().tolist()
            
    return results

def extract_keyword(text):
    #Uses spacy to extract keywords from description to better support weighting of final score
    _nlp, _, _ = get_resources()
    doc = _nlp(text)
    return [t.lemma_.lower() for t in doc if t.pos_ in ["NOUN", "ADJ"] and not t.is_stop]

# --- MATH FUNCTIONS --- #CHECK IF PYTHON HAS A LIBRARY FOR THIS 

def cosine_similarity(feat1, feat2):
    """Math-based similarity for vectors (tensors or lists)."""

    if feat1 is None or feat2 is None:
        return 0.0

    # Ensure inputs are tensors (pgvector might return numpy arrays)
    if isinstance(feat1, (list, np.ndarray)): feat1 = torch.tensor(feat1).to(device)
    if isinstance(feat2, (list, np.ndarray)): feat2 = torch.tensor(feat2).to(device)
    

    # # Ensure inputs are tensors
    # if isinstance(feat1, list): feat1 = torch.tensor(feat1).to(device)
    # if isinstance(feat2, list): feat2 = torch.tensor(feat2).to(device)
    
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
    Main matching logic for system UWI Lost and Found.
    Handles Vision-to-Vision, Text-to-Text, and Cross-Modal (Text-to-Vision) matching.
    """

    # Extracts Categories from Database 
    lost_cat = lost_report.description.item_type
    found_cat = found_report.description.item_type
    
    # If Categories don't match an exit is made ( eg. Computers and Electionics with Clothing)
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

    # Extracts the text descriptions from each report 
    l_text = lost_report.description.text_description or ""
    f_text = found_report.description.text_description or ""
    
    # Cleans up the results for AI usage 
    if f_text.lower() == "no description":
        f_text = "" 

    # The Scoring Logic 

    # Keyword Score (spaCy)

    """
    Extracts the Key Words from each Report and Applies Keyword Similarity Function to 
    calculate a Key Word Score. 
    """
    l_keys = extract_keyword(l_text)
    f_keys = extract_keyword(f_text)
    kw_score = keyword_similarity(l_keys, f_keys)



    # Text Similarity Score (CLIP Text-to-Text)

    """
    Extracts the text_embeddings from both the lost and found reports to apply 
    the cosine similarity function in order to get the text_score from the vector 
    embeddings stored in the database 
    """

    text_score = 0
    if lost_report.description.text_embed is not None and found_report.description.text_embed is not None and f_text != "":
        text_score = cosine_similarity(
            lost_report.description.text_embed, 
            found_report.description.text_embed
        )

    # Image Score (CLIP Vision-to-Vision OR Cross-Modal)

    """
    Extracts image_embeddings and text_embeddings from the lost and found reports to apply
    cosine similarity function 

    User Upload :  

    1. If both have image_embeddings -> Image to Image Scoring 
    2. If lost report has text_embedding and found report has image_embedding -> Image to Text Scoring 

    """

    img_score = 0
    l_img_vec = getattr(lost_report.description, 'image_embed', None)
    f_img_vec = getattr(found_report.description, 'image_embed', None)
    l_text_vec = lost_report.description.text_embed

    if l_img_vec is not None and f_img_vec is not None:
        # Scenario A: Both have images
        img_score = cosine_similarity(l_img_vec, f_img_vec)
    elif l_text_vec is not None and f_img_vec is not None:
        # Scenario B: Lost has text, Found has image (Cross-Modal)
        img_score = cosine_similarity(l_text_vec, f_img_vec)

    # 4. Final Score Calculation 

    # Scenario 1: Found Item has no usable text description
    if not f_text:
        final_score = img_score
        if l_img_vec is not None and f_img_vec is not None:
            high_threshold = 0.65 # Similarity above 65% ->  a high match.
            potential_threshold = 0.50 # Similarity above 50% -> a potential match.
        else:
            # Cross-modal thresholds (lower due to different vector spaces)
            high_threshold = 0.35 #Similarity above 35% ->  a high match.
            potential_threshold = 0.28 # Similarity above 28% -> a potential match.

    # Scenario 2: Both have full data (Text + Image)
    elif img_score > 0 and text_score > 0:
        """
        Image Score takes up most of the Weight -> 60% 
        Text Score takes the next big segment of Weight  -> 30%
        Key word Score takes least of Weight -> 10%
        """
        final_score = (0.6 * img_score) + (0.3 * text_score) + (0.1 * kw_score)
        high_threshold = 0.60
        potential_threshold = 0.45
    
    # Scenario 3: Fallback (Text-to-Text only)
    else:
        """
        Text Score takes up most of the Weight -> 80%
        Key Word Score takes up least of the Weight -> 20% 
        """
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