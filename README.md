# Crypto Data Lakehouse

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8.1-017CEE.svg?logo=apache-airflow)
![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.1-E25A1C.svg?logo=apache-spark)
![MinIO](https://img.shields.io/badge/MinIO-S3_Compatible-C7202C.svg?logo=minio)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B.svg?logo=streamlit)

## Description du Projet
Ce projet implémente une architecture Data Lakehouse de bout en bout pour l'ingestion, la transformation et la visualisation en temps quasi-réel des données du marché des crypto-monnaies (Bitcoin et Ethereum). 

Il applique les meilleures pratiques de l'ingénierie des données, notamment l'architecture Médaillon (Bronze, Silver, Gold), et assure un découplage total entre la couche de stockage (MinIO) et la couche de calcul distribué (Apache Spark). L'ensemble du pipeline est automatisé et orchestré par Apache Airflow.

## Architecture Technique

Le pipeline est conteneurisé et s'exécute de manière séquentielle toutes les 15 minutes :

1. **Couche Bronze (Ingestion) :** Extraction des données brutes depuis l'API CoinGecko via des scripts Python natifs. Les données sont ingérées et stockées à l'état brut dans MinIO.
2. **Couche Silver (Transformation) :** Nettoyage, typage et structuration des données à l'aide d'Apache Spark. Création d'une source de vérité unifiée sauvegardée au format optimisé `.parquet`.
3. **Couche Gold (Agrégation) :** Création de vues métiers par Apache Spark (prix maximum, volumes sur 24h, calculs de variations) pour optimiser les performances de lecture.
4. **Couche Présentation :** Un tableau de bord interactif développé avec Streamlit lit directement les fichiers Parquet de la couche Gold pour visualiser les indicateurs clés en direct.

## Stack Technologique
* **Orchestration :** Apache Airflow (LocalExecutor)
* **Traitement distribué :** Apache Spark (Cluster Local Master/Worker)
* **Stockage Objet :** MinIO (S3 Compatible)
* **Visualisation :** Streamlit, Plotly, Pandas, PyArrow
* **Infrastructure :** Docker & Docker Compose

## Structure du Dépôt

```text
crypto-data-lakehouse/
├── dags/                   # Définition des graphes d'exécution (DAGs Airflow)
├── Scripts/                   # Scripts ETL et code source de l'application
│   ├── ingestion.py        # Script d'extraction (Bronze)
│   ├── transformation_silver.py
│   ├── transformation_gold.py
│   └── app.py              # Application Streamlit
├── docker-compose.yml      # Configuration de l'infrastructure
├── .gitignore              # Règles d'exclusion Git
└── README.md               # Documentation du projet
