import pandas as pd
import re
from datetime import datetime
from typing import Literal
from pathlib import Path
import os


def multi_replace(
    df: pd.DataFrame, column: str, replace_regex_dict: dict
) -> pd.DataFrame:
    def helper(text, replacements):
        pattern = re.compile("|".join(re.escape(k) for k in replacements.keys()))
        return pattern.sub(lambda m: replacements[m.group(0)], text)

    df_copy = df.copy()
    df_copy[column] = df_copy[column].apply(lambda x: helper(x, replace_regex_dict))
    return df_copy


def uppercase_first_letter(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df_copy = df.copy()
    df_copy[column] = df_copy[column].apply(
        lambda x: x[0].upper() + x[1:] if isinstance(x, str) and len(x) > 0 else x
    )
    return df_copy


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df_copy = df.copy()
    # Преобразуем обжект в стринги
    for col in df_copy.columns:
        if df_copy[col].dtype == "object":
            df_copy[col] = df_copy[col].astype("string")

    # Удаляем всякое г до и после строки
    df_copy = df_copy.map(
        lambda v: re.sub(r"^\s+|\s+$", "", v) if isinstance(v, str) else v
    )
    # Удаляем переносы везде (зачем они?)
    df_copy = df_copy.map(
        lambda v: v.strip().replace("\n", " ") if isinstance(v, str) else v
    )

    df_copy = df_copy.rename(
        mapper=lambda v: re.sub(r"^[^a-zA-Zа-яА-Я№]+", "", v),
        axis="columns",
    )
    return df_copy


def classification(
    df: pd.DataFrame, replace_dict: dict, column_from: str, column_to: str
) -> pd.DataFrame:
    def replace_val(value):
        for replace_string, replace_values in replace_dict.items():
            for val in replace_values:
                if val.lower() in value.lower():
                    return replace_string
        return value

    df_copy = df.copy()
    df_copy[column_to] = df_copy[column_from].apply(replace_val)

    #   not_replaced_values = df_copy[df_copy[column_to].isin(replace_dict.keys()) == False][  # noqa: E712
    #       column_from
    #   ].unique()
    return df_copy


def null_replacement(
    df: pd.DataFrame,
    replace_dict: dict | None = None,
    mode: Literal["column", "type"] = "column",
) -> pd.DataFrame:
    df_copy = df.copy()
    if mode == "column":
        for column, replace_with in replace_dict.items():
            df_copy[column] = df_copy[column].fillna(value=replace_with)
    else:
        for column in df_copy.columns:
            if pd.api.types.is_numeric_dtype(df_copy[column]):
                df_copy[column] = df_copy[column].fillna(0)
            elif pd.api.types.is_string_dtype(
                df_copy[column]
            ) or pd.api.types.is_object_dtype(df_copy[column]):
                df_copy[column] = df_copy[column].fillna("-")
    return df_copy


def type_conversion(df: pd.DataFrame, conversion_dict: dict) -> pd.DataFrame:
    df_copy = df.copy()
    for column, convert_to in conversion_dict.items():
        df_copy[column] = df_copy[column].astype(convert_to)
    return df_copy


def set_month_names(
    df: pd.DataFrame, month_column_int: str, month_column_str: str
) -> pd.DataFrame:
    month_names = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }
    df_copy = df.copy()
    df_copy[month_column_str] = df_copy[month_column_int].astype(int).map(month_names)
    return df_copy


def extract_month_and_year(file_name: str):
    month_names = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }
    str_date = file_name.split("_")[1]
    date = datetime.strptime(str_date, "%d-%m-%Y")
    month, year = date.month, date.year
    return month_names[month], year


def parse_filename(filename: str, save_extension: Literal["parquet"] = None):
    """
    Парсит имя файла для получения пути сохранения.

    Пример: something_06-06-2021.xlsx -> something/2021/06/something_06-06-2021.xlsx
    """
    try:
        # Ищем дату в формате DD-MM-YYYY в имени файла
        match = re.search(r"(.+)_(\d{2})-(\d{2})-(\d{4})\.(xlsx|csv)$", filename)

        if match:
            prefix = match.group(1)
            day = match.group(2)
            month = match.group(3)
            year = match.group(4)
            extension = match.group(5)

            # Формируем путь: prefix/year/month/original_filename
            if not save_extension:
                return f"{prefix}/{year}/{month}/{filename}"
            return f"{prefix}/{year}/{month}/{Path(filename).stem}.{save_extension}"
        else:
            # Если не удалось распарсить, используем prefix/ как путь
            prefix = filename.split("_")[0] if "_" in filename else "chore"
            if not save_extension:
                return f"{prefix}/{filename}"
            return f"{prefix}/{Path(filename).stem}.{save_extension}"
    except Exception:
        return f"chore/{filename}"


def create_bucket_file_path(dasboard_name: str, original_file_name: str):
    now = datetime.now()
    file_name = Path(original_file_name).stem.strip()
    file_ext = os.path.splitext(original_file_name)[1]
    year = now.year
    month = now.month
    day = now.day
    if dasboard_name:
        return f"{dasboard_name}/{year}/{month}/{file_name}_day{day}_id{now.timestamp():.0f}{file_ext}"
    return f"trash/{original_file_name}"
