from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.constants import (
    DASHBOARDS,
    RegistrationCallback,
    SETTINGS_STRUCTURE,
    SettingsCallback,
)


def main_loader_kb():
    builder = InlineKeyboardBuilder()
    for text, callback in DASHBOARDS:
        builder.button(text=text, callback_data=callback)
    builder.adjust(3, 3, 1, 1, 1, 1)
    return builder.as_markup()


def goback_actions_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить выбор", callback_data="back")],
            [
                InlineKeyboardButton(
                    text="📖 Показать инструкцию", callback_data="show_instruction"
                )
            ],
        ]
    )


def register_request_kb(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Принять",
        callback_data=RegistrationCallback(
            action="a",
            user_id=user_id,
        ),
    )
    builder.button(
        text="❌ Отклонить",
        callback_data=RegistrationCallback(
            action="r",
            user_id=user_id,
        ),
    )
    builder.adjust(1, 1)
    return builder.as_markup()


def generate_settings_kb(level, back=False):
    builder = InlineKeyboardBuilder()
    if not back:
        for option, callback in SETTINGS_STRUCTURE[level].items():
            builder.button(
                text=option,
                callback_data=SettingsCallback(level=level, option=callback),
            )
        builder.adjust(1, True)
        return builder.as_markup()
    else:
        builder.button(
            text="Назад", callback_data=SettingsCallback(level=level, option="back")
        )
        builder.adjust(1, True)
        return builder.as_markup()


def settings_confirm_action_kb(level):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Потвердить",
                    callback_data=SettingsCallback(
                        level=level, option="confirm"
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=SettingsCallback(level=level, option="cancel").pack(),
                )
            ],
        ]
    )


def generate_online_url_button(url: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🛢️ Перейти в Minio", url=url)]]
    )
