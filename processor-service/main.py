from contextlib import asynccontextmanager
import urllib
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Query
import logging
from pathlib import Path
import os

from s3.client import get_file_as_df_from_s3, put_df_to_s3, s3_client
from etl.pipeline import run_dlt_pipeline
from processing.processing_funcs import procces_df
from processing.helpers import create_bucket_file_path, read_json, save_json
from processing.constants import RAW_BUCKET_NAME, PROCESSED_BUCKET_NAME, DasboardName

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
processing_cfg = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    loaded_cfg = await read_json(CONFIG_PATH)
    processing_cfg.update(loaded_cfg)
    logger.info(
        f"Config Loaded for {','.join(processing_cfg.keys()).removesuffix(',')}"
    )
    yield
    logger.info("App Down")


app = FastAPI(lifespan=lifespan)
logger = logging.getLogger("uvicorn.error")


@app.get("/")
async def root():
    return {"api": "ok"}


@app.get("/get_config")
async def get_config(
    dashboard_name: DasboardName = Query(default=DasboardName.wout_category),
):
    return {
        "config": processing_cfg.get(
            dashboard_name.value, f"Config not set for {dashboard_name.value}"
        )
    }


@app.post("/set_config")
async def set_config(
    config: dict,
    dashboard_name: DasboardName = Query(default=DasboardName.wout_category),
):
    if dashboard_name.value in processing_cfg.keys():
        processing_cfg[dashboard_name.value] = config
        return {"status:": "ok"}
    return {"status": "fail"}


@app.post("/save_config")
async def save_config():
    try:
        await save_json(processing_cfg, CONFIG_PATH)
        return {"status": "ok", "save_path": CONFIG_PATH}
    except Exception as e:
        return {"status": "fail", "exception": str(e)}


@app.post("/load_config")
async def load_config():
    try:
        loaded_cfg = await read_json(CONFIG_PATH)
        processing_cfg.update(loaded_cfg)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "fail", "exception": str(e)}


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
        return {"status": "success", "key": path, "ui_path": minio_ui_path}

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
    object_key = urllib.parse.unquote(
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
    processed_path = (os.path.splitext(object_key)[0] + ".parquet").replace("+", " ")
    dataset_name = Path(object_key).parts[0]
    # ---------------------------------

    # Обрабатываем файл
    try:
        df = get_file_as_df_from_s3(object_key)
        logger.info(f"Received file {file_name_ext} as df")
        processed_df = procces_df(
            df, dataset_name, process_config=processing_cfg.get(dataset_name)
        )
        put_df_to_s3(processed_path, processed_df)
        logger.info(
            f"Processed and Saved file to {Path(processed_path).parent} as {os.path.split(processed_path)[-1]}"
        )
    except Exception as e:
        logger.error(str(e))
    return {
        "status": "sucess",
    }


@app.post("/process_all_files")
async def process_all_files(
    dashboard_name: DasboardName = Query(default=DasboardName.wout_category),
):
    response = s3_client.list_objects(
        Bucket=RAW_BUCKET_NAME, Prefix=dashboard_name.value
    )
    logger.info(processing_cfg)
    contents = response.get("Contents")
    file_keys = [d.get("Key") for d in contents]
    dataset_name = dashboard_name.value

    for key in file_keys:
        try:
            df = get_file_as_df_from_s3(key)
            processed_df = procces_df(
                df, dataset_name, process_config=processing_cfg[dataset_name]
            )
            processed_path = os.path.splitext(key)[0] + ".parquet"
            put_df_to_s3(processed_path, processed_df)
        except Exception as e:
            logger.info(f"Error when processing {key}: {e}")
            return {"status": "fail", "exception": e}

    return {"status": "ok", "processed_files": file_keys}
