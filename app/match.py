import spacy
import clip
import torch
from PIL import Image

# NLP model
nlp = spacy.load("en_core_web_sm")

#Extracts Keyword using SpAcy 
def extract_keyword(text):
    doc = nlp(text)

    keywords = [
        token.lemma_.lower()
        for token in doc
        if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop
    ]

    return keywords


# Device + CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"

model, preprocess = clip.load("ViT-B/32", device=device)
model.eval()


# IMAGE ENCODING
def encode_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image)

    return image_features


# TEXT ENCODING
def encode_text(text):
    text_tokens = clip.tokenize([text]).to(device)

    with torch.no_grad():
        text_features = model.encode_text(text_tokens)

    return text_features


# SIMILARITY
def cosine_similarity(img_feat, text_feat):
    img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
    text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)

    return (img_feat @ text_feat.T).item()

#KEY WORD SIMILARITY 
def keyword_similarity(lost_keywords, found_keywords):
    if not lost_keywords or not found_keywords:
        return 0.0

    lost_set = set(lost_keywords)
    found_set = set(found_keywords)

    intersection = lost_set.intersection(found_set)

    return len(intersection) / len(lost_set.union(found_set))

def match_lost_found(lost, found):

    # 1. Text similarity
    lost_text = encode_text(lost.description)
    found_text = encode_text(found.description)
    text_score = cosine_similarity(lost_text, found_text)

    # 2. Image similarity
    lost_img = encode_image(lost.image_path)
    found_img = encode_image(found.image_path)
    image_score = cosine_similarity(lost_img, found_img)

    # 3. Keyword similarity
    lost_keywords = extract_keyword(lost.description)
    found_keywords = extract_keyword(found.description)
    keyword_score = keyword_similarity(lost_keywords, found_keywords)

    # 4. Final weighted score
    
    final_score = (
        0.5 * image_score +
        0.4 * text_score +
        0.1 * keyword_score
    )

    return {
        "image_score": image_score,
        "text_score": text_score,
        "keyword_score": keyword_score,
        "final_score": final_score
    }