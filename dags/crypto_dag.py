from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_engineer',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'crypto_lakehouse_PRODUCTION',
    default_args=default_args,
    start_date=datetime(2026, 6, 14),
    schedule_interval='*/15 * * * *',
    catchup=False,
    tags=['crypto', 'lakehouse', 'spark', 'production'],
) as dag:

    # Phase 1: Ingestion (Airflow exécute nativement le code Python)
    task_bronze = BashOperator(
        task_id='ingestion_bronze',
        bash_command='python /opt/airflow/code/ingestion.py'
    )

    # Phase 2: Transformation Silver (Airflow ordonne à Spark via Docker Exec)
    task_silver = BashOperator(
        task_id='transformation_silver',
        bash_command='docker exec spark-master /opt/spark/bin/spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 /opt/spark/code/transformation_silver.py'
    )

    # Phase 3: Agrégation Gold (Airflow ordonne à Spark via Docker Exec)
    task_gold = BashOperator(
        task_id='transformation_gold',
        bash_command='docker exec spark-master /opt/spark/bin/spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 /opt/spark/code/transformation_gold.py'
    )

    # Définition stricte des dépendances
    task_bronze >> task_silver >> task_gold