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