import os
import spacy
import spacy.cli
import requests
import numpy as np
from io import BytesIO


# THIS IS INCASE WE WANT TO RUN CLIP OVER CLOUD 
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/openai/clip-vit-base-patch32"

# Global spaCy only — no more CLIP/torch model loading
nlp = None


def get_nlp():
    global nlp
    if nlp is None:
        print("🔍 Loading spaCy...")
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
    return nlp


# --- ENCODING FUNCTIONS ---

def _hf_text_embedding(text):
    response = requests.post(
        HF_API_URL,
        headers={"Authorization": f"Bearer {HF_TOKEN}"},
        json={"inputs": text}
    )
    response.raise_for_status()
    return response.json()


def _hf_image_embedding(image_url):
    img_bytes = requests.get(image_url).content
    response = requests.post(
        HF_API_URL,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "image/jpeg"
        },
        data=img_bytes
    )
    response.raise_for_status()
    return response.json()


def generate_embeddings(text=None, image_url=None):
    """
    Called in views.py when a user SUBMITS a report.
    Now fetches embeddings from Hugging Face instead of local CLIP.
    """
    results = {"text_vec": None, "image_vec": None}

    if text:
        results["text_vec"] = _hf_text_embedding(text)

    if image_url:
        results["image_vec"] = _hf_image_embedding(image_url)

    return results


def extract_keyword(text):
    doc = get_nlp()(text)
    return [t.lemma_.lower() for t in doc if t.pos_ in ["NOUN", "ADJ"] and not t.is_stop]


# --- MATH FUNCTIONS (numpy instead of torch — no GPU needed) ---

def cosine_similarity(feat1, feat2):
    v1 = np.array(feat1, dtype=np.float32)
    v2 = np.array(feat2, dtype=np.float32)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def keyword_similarity(lost_keywords, found_keywords):
    if not lost_keywords or not found_keywords:
        return 0.0
    ls, fs = set(lost_keywords), set(found_keywords)
    return len(ls.intersection(fs)) / len(ls.union(fs))


def match_lost_found(lost_report, found_report):
    """
    Unchanged — still works off stored DB embeddings.
    No CLIP or HF calls happen here.
    """
    lost_cat  = lost_report.description.item_type
    found_cat = found_report.description.item_type

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

    l_text = lost_report.description.text_description or ""
    f_text = found_report.description.text_description or ""
    if f_text.lower() == "no description":
        f_text = ""

    l_keys   = extract_keyword(l_text)
    f_keys   = extract_keyword(f_text)
    kw_score = keyword_similarity(l_keys, f_keys)

    text_score = 0
    if lost_report.description.text_embedding and found_report.description.text_embedding and f_text:
        text_score = cosine_similarity(
            lost_report.description.text_embedding,
            found_report.description.text_embedding
        )

    img_score  = 0
    l_img_vec  = getattr(lost_report.description, 'image_embedding', None)
    f_img_vec  = getattr(found_report.description, 'image_embedding', None)
    l_text_vec = lost_report.description.text_embedding

    if l_img_vec and f_img_vec:
        img_score = cosine_similarity(l_img_vec, f_img_vec)
    elif l_text_vec and f_img_vec:
        img_score = cosine_similarity(l_text_vec, f_img_vec)

    if not f_text:
        final_score = img_score
        high_threshold      = 0.65 if (l_img_vec and f_img_vec) else 0.35
        potential_threshold = 0.50 if (l_img_vec and f_img_vec) else 0.28
    elif img_score > 0 and text_score > 0:
        final_score         = (0.6 * img_score) + (0.3 * text_score) + (0.1 * kw_score)
        high_threshold      = 0.60
        potential_threshold = 0.45
    else:
        final_score         = (0.8 * text_score) + (0.2 * kw_score)
        high_threshold      = 0.55
        potential_threshold = 0.40

    match_status = "none"
    if final_score >= high_threshold:
        match_status = "high"
    elif final_score >= potential_threshold:
        match_status = "potential"

    return {
        "final_score":    round(final_score, 4),
        "match_status":   match_status,
        "is_high_match":  match_status == "high",
        "threshold_used": high_threshold,
        "image_score":    round(img_score, 4),
        "text_score":     round(text_score, 4),
        "keyword_score":  round(kw_score, 4),
        "lost_category":  lost_cat,
        "found_category": found_cat,
        "category_match": True
    }