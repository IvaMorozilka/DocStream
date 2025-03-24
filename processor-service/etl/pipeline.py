import dlt
import requests
import json
import os
from decouple import config
import logging
from dlt.sources.filesystem import readers

from processing.constants import EN_TABLE_NAMES_NORMALIZED

logger = logging.getLogger("uvicorn.error")


def get_token():
    login_url = f"{config('DREMIO_API_URL')}/apiv2/login"
    headers = {"Content-Type": "application/json"}
    payload = {
        "userName": config("DREMIO_USER"),
        "password": config("DREMIO_PASSWORD"),
    }

    try:
        response = requests.post(login_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        json_response = response.json()

        if "token" in json_response:
            os.environ["DREMIO_TOKEN"] = json_response["token"]
        elif "errorMessage" in json_response:
            logger.error(f"Authentication Error: {json_response['errorMessage']}")
        else:
            logger.error(f"Unexpected response format: {json_response}")
    except Exception as e:
        logger.error(f"Request error during login: {e}")


def update_table_metadata(dataset_name: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"_dremio{os.environ.get('DREMIO_TOKEN')}",
    }

    sql_query = f'ALTER TABLE Datasets."{EN_TABLE_NAMES_NORMALIZED[dataset_name]}"."all_data" REFRESH METADATA'
    payload = {"sql": sql_query}
    try:
        response = requests.post(
            f"{config('DREMIO_API_URL')}/api/v3/sql",
            headers=headers,
            data=json.dumps(payload),
        )
        response.raise_for_status()
        json_response = response.json()
        if "errorMessage" in json_response:
            logger.error(f"Metadata update failed: {json_response['errorMessage']}")
        else:
            logger.info(f"Metadata for table {dataset_name} updated successfully!")
        return False
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.info("Authentication failed (401). Attempting to refresh token...")
            return True
        else:
            logger.error(f"HTTP Error: {e}")


@dlt.source
def minio_source(dataset_name: str):
    if dataset_name == "ГуманитарнаяПомощьСВО":
        parquet_reader = readers(
            file_glob=f"{dataset_name}/**/*.parquet",
        ).read_parquet()
        parquet_reader.apply_hints(write_disposition="replace")
        return parquet_reader.with_name("all_data")

    return None


# Функция для запуска DLT пайплайна
def run_dlt_pipeline(dataset_name: str):
    # Настройка и запуск dlt пайплайна
    pipeline = dlt.pipeline(
        pipeline_name="main",
        destination="postgres",
        dataset_name=EN_TABLE_NAMES_NORMALIZED.get(dataset_name),
    )

    load_info = pipeline.run(minio_source(dataset_name))

    # Обновляем метаданные
    if not os.environ.get("DREMIO_TOKEN"):
        get_token()

    try_again = update_table_metadata(dataset_name)
    if try_again:
        get_token()
        update_table_metadata(dataset_name)

    return load_info
