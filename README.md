# UWI-lost-and-found-system

COMP3901 Capstone Project 

## 📌 Project Title & Description

Lost & Found Matching System (AI-Powered with CLIP)

This project is a full-stack Lost & Found system designed to help users report, search, and match lost items using both text and image data. It uses an AI-powered embedding model (OpenAI CLIP) to compare similarity between reports, enabling more accurate matching beyond simple keyword search.

The system allows users to submit lost or found items with descriptions and images. These inputs are converted into embeddings using CLIP and stored in a PostgreSQL database enhanced with the pgvector extension. The backend then performs similarity matching to suggest potential matches in real time.

The goal of this project is to improve traditional lost-and-found systems by introducing multimodal AI matching (text + image understanding), making it easier to reconnect items with their owners.

## 👥 Group Members 

| Member | ID | Role |
|----------|----------|----------|
| Ashani Mae | 620054256  | Frontend  |
| Jada-Marie Dotting  | 620166370 | Frontend |
| Ashle Johnson  | 620164713 | Backend  |
| Gabriel Smith  | 620162866 | Backend  |


## 🛠️ Tech Stack

### Backend
Python 🐍
Flask
SQLAlchemy
PostgreSQL

### AI / ML
OpenAI CLIP (ViT-B/32)
PyTorch
pgvector (vector similarity search)

### DevOps / Infrastructure
Docker & Docker Compose
PostgreSQL containerized database
Other Tools
Werkzeug (authentication / password hashing)
Python dotenv (.env configuration)

## ⚙️ Setup Instructions

### 1. Start Docker Database

```bash
docker-compose up -d
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate 
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
Use .sample-env file for setup 
```

### 5. Initialize database (IMPORTANT)

Run setup script:

```bash
python setup_db.py
```

This will:
Enable pgvector
Create all tables
Generate 100 test users


### 6. Run the application

```bash
flask run 
```

### ⚠️ Notes

Running setup.py will reset the database (drop_all() is used)
First CLIP execution may download the model (~350MB)
Ensure Docker is running before starting the backend
pgvector must be enabled for similarity search to work

### CLIP Model Setup Notes (Automatic)

This project uses OpenAI’s CLIP model (ViT-B/32).

The model is NOT required to be manually downloaded
It will be automatically loaded on first run of the embedding service
If not cached locally, it will be downloaded (~350MB)

### 👤 Users 

Our system mimics UWI's ID Number system but specifically 

Admin -> 620000001, 620000002, 620000003, 620000004, 620000005

General user ->  620000005 < 

Password -> password123 