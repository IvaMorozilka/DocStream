from decouple import config

# Для настройки клиента s3
S3_ENDPOINT_URL = config("S3_ENDPOINT_URL")
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
RAW_BUCKET_NAME = config("RAW_BUCKET_NAME")
PROCESSED_BUCKET_NAME = config("PROCESSED_BUCKET_NAME")


# Названия дашбордов на английском
EN_TABLE_NAMES_NORMALIZED = {
    "ГуманитарнаяПомощьСВО": "hummanitarian_aid_svo",
    "АИП": "aip",
}

# Названия колонок на английском
# Гумантирная помощь
EN_HASVO_COLS = {
    "№ п/п": "item_no",
    "Дата передачи имущества": "date",
    "Наименование материальны средств (оказанных услуг)": "name_of_material_assets",
    "Марка, модель передаваемых материальных средств": "brand_model_of_material_assets",
    "Ед. изм.": "unit",
    "Потребность по поступившей заявке в/ч": "need",
    "Отправитель заявки": "request_sender",
    "Кол-во переданного имущества": "quantity",
    "Кому передано имущество (оказаны услуги)": "to_whom",
    "Затраченные финансовые средщства, тыс. руб": "spent_financial_resources",
    "Кол-во не реализованного по заявке имущества": "quantity_of_unfulfilled_request_assets",
    "Субъект РФ": "subject",
    "ОИВ субъекта РФ (организация), осуществляющая закупку": "government_body",
    "Сведения о контрагенте (наименование организации, телефон, сайт)": "information_about_the_organization",
    "Что передали": "what_was_transferred",
    "Год": "year",
    "Месяц": "month",
    "Месяц_назв": "month_name",
    "Сколько запросили в еденицах": "quantity_requested",
    "Сколько передали в еденицах": "quantity_transferred",
}
