from pyspark.sql import SparkSession

print("Initialisation de Spark pour la couche Gold...")

# --- 1. Configuration de la session Spark ---
spark = SparkSession.builder \
    .appName("Silver_to_Gold_Crypto") \
    .master("spark://spark-master:7077") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "password") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# --- 2. Lecture de la couche Silver ---
print("Lecture des données Silver (Parquet)...")
df_silver = spark.read.parquet("s3a://silver/market_data/coingecko/")

# On transforme le DataFrame en une table SQL virtuelle
df_silver.createOrReplaceTempView("silver_crypto")

# --- 3. Transformation Métier (SQL pur) ---
print("Exécution de la logique métier (SQL)...")

# Requête type "dbt" : on convertit les dates pour le Dashboard 
# et on calcule un nouvel indicateur (le volume total des 3 cryptos)
query_gold = """
    SELECT 
        CAST(ingestion_timestamp AS TIMESTAMP) AS exact_time,
        DATE(CAST(ingestion_timestamp AS TIMESTAMP)) AS date_jour,
        bitcoin_price,
        bitcoin_vol,
        ethereum_price,
        ethereum_vol,
        solana_price,
        solana_vol,
        (bitcoin_vol + ethereum_vol + solana_vol) AS total_market_volume_top3
    FROM silver_crypto
"""

df_gold = spark.sql(query_gold)

print("Aperçu de la table finale Gold (Prête pour le Dashboard) :")
df_gold.show(truncate=False)

# --- 4. Écriture dans la couche Gold ---
print("Sauvegarde dans le bucket Gold...")
output_path = "s3a://gold/market_data/coingecko_summary/"

df_gold.write \
    .mode("overwrite") \
    .parquet(output_path)

print(f"Succès ! La table métier est disponible dans {output_path}")

spark.stop()