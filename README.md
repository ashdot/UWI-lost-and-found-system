# UWI-lost-and-found-system
COMP3901 Capstone Project 

Group Members 

Ashani Mae 
Jada-Marie Dotting
Ashle Johnson 
Gabriel Smith 

## Setup Instructions 

1. Setup Flask 
2. Download Requirements.txt 
3. Download CLIP model - ViT-B-32.pt if running locally ( command is )
4. SETUP env. FILE 
5. SETUP database file -> Ensure PostGres is Installed 
6. Ensure 

"This project uses the OpenAI CLIP (ViT-B/32) model. Upon the first execution of generate_embeddings, the system will attempt to load the model locally from the root directory. If not found, it will automatically fetch it from OpenAI's public servers. Total file size is ~350MB."


docker-compose up -d
docker-compose exec db psql -U postgres -d lost_and_found -c "CREATE EXTENSION IF NOT EXISTS vector;"
