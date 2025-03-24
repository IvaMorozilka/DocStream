import urllib.parse
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Query
import logging
import urllib
from pathlib import Path
import re
import os
from enum import Enum

from s3.client import get_file_as_df_from_s3, put_df_to_s3, s3_client
from etl.pipeline import run_dlt_pipeline
from processing.processing_funcs import procces_df
from processing.helpers import (
    extract_month_and_year,
    parse_filename,
    create_bucket_file_path,
)
from processing.constants import RAW_BUCKET_NAME, PROCESSED_BUCKET_NAME


app = FastAPI()
logger = logging.getLogger("uvicorn.error")


class DasboardName(str, Enum):
    gummanitarnaya_pomoshch_svo = "ГуманитарнаяПомощьСВО"
    aip = "АИП"
    oep = "ОЭП"
    kok = "КОК"
    fns = "ФНС"
    kcr = "КЦР"
    oiv = "ОИВ"
    soczashchita = "Соцзащита"
    novyj_fns = "НовыйФНС"
    importozameshchenie = "Импортозамещение"
    wout_category = ""


@app.get("/")
async def root():
    return {"api": "sucess"}


@app.post("/upload_file/")
async def upload(
    dashboard_name: DasboardName = Query(default=DasboardName.wout_category),
    file: UploadFile = File(...),
):
    if not file.filename.endswith((".xlsx", ".csv")):
        raise HTTPException(
            status_code=400, detail="Поддерживаются только .xlsx и .csv файлы"
        )
    try:
        file_content = await file.read()
        original_filename = urllib.parse.unquote(file.filename)

        path = create_bucket_file_path(dashboard_name.value, original_filename)
        s3_client.put_object(
            Bucket=RAW_BUCKET_NAME,
            Key=path,
            Body=file_content,
            ContentType=file.content_type,
        )
        minio_ui_path = f"/browser/{RAW_BUCKET_NAME}/{urllib.parse.quote(path)}"
        return {"status": "success", "path": minio_ui_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/raw_file_deleted")
async def handle_delete(request: Request):
    event_data = await request.json()
    object_key = urllib.parse.unquote(
        (event_data.get("Records", [{}])[0].get("s3", {}).get("object", {}).get("key"))
    )
    s3_client.delete_object(
        Bucket=PROCESSED_BUCKET_NAME, Key=os.path.splitext(object_key)[0] + ".parquet"
    )
    return {"status": "sucess"}


@app.post("/run_pipeline")
async def run_pipeline(request: Request):
    event_data = await request.json()
    object_key = (
        event_data.get("Records", [{}])[0].get("s3", {}).get("object", {}).get("key")
    )

    dataset_name = Path(object_key).parts[0]
    try:
        load_info = run_dlt_pipeline(dataset_name)
        logger.info(str(load_info))
        return {"status": "sucess"}
    except Exception:
        logger.error(str(load_info))
        return {"status": "fail"}


@app.post("/process_new_file")
async def process_file(request: Request):
    # Получаем информацию из реквеста
    event_data = await request.json()
    object_key = urllib.parse.unquote(
        (event_data.get("Records", [{}])[0].get("s3", {}).get("object", {}).get("key"))
    )
    file_name_ext = Path(object_key).name
    processed_path = os.path.splitext(object_key)[0] + ".parquet"
    dataset_name = Path(object_key).parts[0]
    # ---------------------------------

    # Обрабатываем файл
    try:
        df = get_file_as_df_from_s3(object_key)
        logger.info(f"Received file {file_name_ext} as df")
        processed_df = procces_df(df, dataset_name)
        put_df_to_s3(processed_path, processed_df)
        logger.info(
            f"Processed and Saved file to {Path(processed_path).parent} as {os.path.split(processed_path)[-1]}"
        )
    except Exception as e:
        logger.error(str(e))
    return {"status": "sucess"}
