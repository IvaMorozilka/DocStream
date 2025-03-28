import pandas as pd
import os
import logging

import processing.helpers as helpers
from processing.constants import EN_HASVO_COLS, DasboardName


def humanitarian_aid(df: pd.DataFrame, process_config: dict):
    rename_data = process_config.get("rename_data")

    df = helpers.prepare(df)
    df = helpers.classification(
        df,
        rename_data,
        "Наименование материальны средств (оказанных услуг)",
        "Что передали",
    )
    df = helpers.null_replacement(df, mode="type")
    df = helpers.type_conversion(
        df,
        {
            "№ п/п": "int64",
            "Кол-во переданного имущества": "Int64",
            "Кол-во не реализованного по заявке имущества": "Int64",
            "Затраченные финансовые средщства, тыс. руб": "float64",
        },
    )

    # Военные замены: Отправитель заявки, Кому передано имущество (оказаны услуги)
    voen_regex = process_config.get("voen_regex")

    # ОИВ субъекты: ОИВ субъекта РФ (организация), осуществляющая закупку, Сведения о контрагенте (наименование организации, телефон, сайт)
    oiv_regex = process_config.get("oiv_regex")

    df = helpers.multi_replace(df, "Отправитель заявки", voen_regex)
    df = helpers.multi_replace(
        df, "Кому передано имущество (оказаны услуги)", voen_regex
    )
    df = helpers.multi_replace(
        df, "ОИВ субъекта РФ (организация), осуществляющая закупку", oiv_regex
    )
    df = helpers.multi_replace(
        df,
        "Сведения о контрагенте (наименование организации, телефон, сайт)",
        oiv_regex,
    )
    df = helpers.uppercase_first_letter(
        df, "Наименование материальны средств (оказанных услуг)"
    )
    df = helpers.uppercase_first_letter(
        df, "ОИВ субъекта РФ (организация), осуществляющая закупку"
    )
    df = helpers.uppercase_first_letter(
        df, "Сведения о контрагенте (наименование организации, телефон, сайт)"
    )
    df["Кол-во не реализованного по заявке имущества"] = (
        df["Потребность по поступившей заявке в/ч"] - df["Кол-во переданного имущества"]
    )

    df["Год"] = df["Дата передачи имущества"].dt.year.astype(str)
    df["Месяц"] = df["Дата передачи имущества"].dt.month.astype(str)

    df = helpers.type_conversion(
        df,
        {
            "Месяц": "int64",
        },
    )

    # Получаем название месяца
    df = helpers.set_month_names(df, "Месяц", "Месяц_назв")

    # Получаем Сколько запросили в еденицах и Сколько передали в еденицах
    df["Сколько запросили в еденицах"] = (
        df["Потребность по поступившей заявке в/ч"].astype(str) + " " + df["Ед. изм."]
    )
    df["Сколько передали в еденицах"] = (
        df["Кол-во переданного имущества"].astype(str) + " " + df["Ед. изм."]
    )
    df["Дата передачи имущества"] = df["Дата передачи имущества"].astype(
        "datetime64[ms]"
    )

    # Дублируем и добавляем все года, все месяца.
    df_d, df_d2, df_d3 = df.copy(), df.copy(), df.copy()

    df_d["Год"] = "Все года"

    df_d2["Месяц_назв"] = "Все месяца"
    df_d2["Месяц"] = 0

    df_d3["Месяц_назв"] = "Все месяца"
    df_d3["Месяц"] = 0
    df_d3["Год"] = "Все года"

    df = pd.concat([df, df_d, df_d2, df_d3], ignore_index=True)
    df.rename(
        columns=EN_HASVO_COLS,
        inplace=True,
    )
    # for row in df.to_dict(orient="records"):  # Итерируемся по строкам
    #     yield row
    return df


def procces_df(
    df: pd.DataFrame, dataset_name: str, process_config: dict
) -> pd.DataFrame:
    if dataset_name == DasboardName.gummanitarnaya_pomoshch_svo.value:
        return humanitarian_aid(df, process_config)
    return df
