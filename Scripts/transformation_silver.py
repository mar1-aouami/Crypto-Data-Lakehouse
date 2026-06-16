from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, map_keys, map_values, lit
from pyspark.sql.types import MapType, StringType, StructType, StructField, DoubleType

print("Initialisation de Spark (téléchargement des connecteurs S3 en cours...)")

# --- 1. Configuration de la session Spark ---
spark = SparkSession.builder \
    .appName("Bronze_to_Silver_Crypto") \
    .master("spark://spark-master:7077") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "password") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# Pour éviter que Spark n'affiche trop de logs inutiles dans la console
spark.sparkContext.setLogLevel("ERROR")

print("Spark est prêt !")

# --- 2. Lecture des données Bronze ---
print("Lecture des fichiers JSON dans le bucket Bronze...")
# On lit tous les fichiers JSON du dossier coingecko
df_bronze = spark.read.json("s3a://bronze/market_data/coingecko/*.json")

# Affichage du schéma brut pour comprendre comment Spark voit les données
print("Schéma de la couche Bronze :")
df_bronze.printSchema()

# --- 3. Transformation (Aplatissement / Flattening) ---
print("Transformation des données...")

# Le JSON de CoinGecko contient les cryptos sous forme de clés dans 'raw_payload'
# On va extraire ces données pour créer des colonnes propres
df_silver = df_bronze.select(
    col("ingestion_timestamp"),
    col("source"),
    # On accède manuellement aux 3 cryptos qu'on a ingérées
    col("raw_payload.bitcoin.usd").alias("bitcoin_price"),
    col("raw_payload.bitcoin.usd_24h_vol").alias("bitcoin_vol"),
    col("raw_payload.ethereum.usd").alias("ethereum_price"),
    col("raw_payload.ethereum.usd_24h_vol").alias("ethereum_vol"),
    col("raw_payload.solana.usd").alias("solana_price"),
    col("raw_payload.solana.usd_24h_vol").alias("solana_vol")
)

print("Aperçu des données nettoyées (Couche Silver) :")
df_silver.show(truncate=False)

# --- 4. Écriture dans la couche Silver (Format Parquet) ---
print("Sauvegarde dans le bucket Silver au format Parquet...")
output_path = "s3a://silver/market_data/coingecko/"

df_silver.write \
    .mode("overwrite") \
    .parquet(output_path)

print(f"Succès ! Les données nettoyées ont été sauvegardées dans {output_path}")

spark.stop()