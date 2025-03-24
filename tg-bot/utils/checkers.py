import re


def check_full_name(full_name: str):
    # 3 слова, из русских букв, каждое с заглавной буквы -> Например: Иванов Иван Иванович
    reg = r"^[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+$"
    return re.match(reg, full_name)


def check_org_name(org_name: str):
    # Пробелы, русские буквы во всех регистрах,символы - " ' « »
    reg = r'^[А-Яа-яЁё0-9\s\'"\-«»]+$'
    return re.match(reg, org_name)
