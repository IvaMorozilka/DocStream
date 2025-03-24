from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_kb():
    kb_list = [
        [KeyboardButton(text="⬇️Загрузить данные")],
        [KeyboardButton(text="🛟Поддержка")],
        [KeyboardButton(text="⚙️Настройки")],
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите пункт",
    )
    return keyboard
