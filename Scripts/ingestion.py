import requests 
import boto3 
import json 
import uuid
from datetime import datetime, timezone
# --- 1. Configuration de la connexion à MinIO ---
s3_client = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='admin',
    aws_secret_access_key='password',
    region_name='us-east-1' # Requis par boto3, même en local
)
# --- 2. Extraction des données (API CoinGecko) ---
print("Extraction des données de l'API CoinGecko...")
response=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum,bitcoin,solana&vs_currencies=usd&include_24hr_vol=true")
if response.status_code == 200:
    raw_data = response.json()
    print("Données extraites avec succès.")
else:
    print("Erreur lors de l'extraction des données.")
# --- 3. Ajout des métadonnées (Source et l'heure d'ingestion)---
payload = {
    "source":"CoinGecko API",
    "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
    "raw_payload": raw_data
}
# --- 4. Chargement dans le Lakehouse (Bucket Bronze) ---
timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
unique_id = uuid.uuid4().hex[:6]
file_name = f"market_data/coingecko/prices_{timestamp_str}_{unique_id}.json"
print("Upload de fichier dans MinIO...")
s3_client.put_object(
    Bucket="bronze",
    Key=file_name,
    Body=json.dumps(payload),
    ContentType='application/json'
)
print(f"Fichier {file_name} uploadé avec succès dans le bucket 'bronze'.")

