import boto3
import pandas as pd
import io
from pathlib import Path

from processing.constants import (
    S3_ENDPOINT_URL,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    RAW_BUCKET_NAME,
    PROCESSED_BUCKET_NAME,
)


s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    use_ssl=False,
)


def get_file_as_df_from_s3(object_key: str, bucket: str = RAW_BUCKET_NAME):
    response = s3_client.get_object(Bucket=bucket, Key=object_key.replace("+", " "))
    file_content = response["Body"].read()
    if Path(object_key).name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_content))
    elif Path(object_key).name.endswith((".xlsx")):
        df = pd.read_excel(io.BytesIO(file_content))
    else:
        raise Exception("Recieved file is not Excel or CSV.")
    return df


def put_df_to_s3(path: str, df: pd.DataFrame, bucket: str = PROCESSED_BUCKET_NAME):
    with io.BytesIO() as buffer:
        df.to_parquet(buffer, index=False)
        buffer.seek(0)
        s3_client.put_object(Bucket=bucket, Key=path, Body=buffer.getvalue())
