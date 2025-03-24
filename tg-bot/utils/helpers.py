from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
import asyncio
from prettytable import PrettyTable, TableStyle

from create_bot import bot, logger
from db_handler.db_funk import get_admins, get_all_users
from keyboards.inline_kbs import generate_online_url_button


async def send_document(
    file_id: str,
    message: Message,
    caption_text: str,
    inline_url: str,
    bot: Bot = bot,
    delete_message_timeout: int = 1,
    show_progress: bool = True,
):
    recievers = await get_admins()
    num_reciever_users = len(recievers)
    sending_text = f"🛫 Отправляю документ...\nПрогресс: {'⚪️' * num_reciever_users}"
    if not show_progress:
        sending_text = sending_text.split("\n")[0]

    sending_msg = await message.answer(text=sending_text)
    ids_without_send = []

    for user_id in [reciever["user_id"] for reciever in recievers]:
        try:
            await bot.send_document(
                chat_id=user_id,  # ID чата пользователя
                document=file_id,  # Открываем сохраненный файл
                caption=caption_text,  # Необязательный текст под файлом
                reply_markup=generate_online_url_button(url=inline_url),
            )
            if show_progress:
                sending_text = sending_text.replace("⚪️", "🟢", 1)
                await bot.edit_message_text(
                    text=sending_text,
                    chat_id=message.chat.id,
                    message_id=sending_msg.message_id,
                )
        except TelegramBadRequest as e:
            logger.error(e)
        except Exception as e:
            logger.error(e)
            ids_without_send.append(user_id)
            if show_progress:
                sending_text = sending_text.replace("⚪️", "🔴", 1)
                await bot.edit_message_text(
                    text=sending_text,
                    chat_id=message.chat.id,
                    message_id=sending_msg.message_id,
                )

        await asyncio.sleep(0.2)

    await asyncio.sleep(delete_message_timeout)
    await bot.delete_message(chat_id=message.chat.id, message_id=sending_msg.message_id)

    return num_reciever_users, ids_without_send


async def send_copy_of_message_to_users(
    bot: Bot,
    message_id: int,
    from_chat_id: int,
    all: bool = True,
    users_ids: list[int] = None,
) -> tuple[int, int]:
    # Получаем всех пользователей из базы данных
    users = await get_all_users()
    users = [user.get("user_id") for user in users]
    if not all:
        users = [user for user in users if user in users_ids]
    # Фильтр, чтобы не дублировалось сообщение в чат
    users = list(filter(lambda user: user != from_chat_id, users))

    successful = 0
    failed = 0

    if not users:
        return 0, 1

    for user_id in users:
        try:
            # Копируем сообщение пользователю
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
                disable_notification=False,
            )
            successful += 1
            # Небольшая задержка для избежания блокировки API
            await asyncio.sleep(0.05)
        except TelegramBadRequest:
            # Обработка ошибки если пользователь заблокировал бота
            failed += 1
        except Exception as e:
            # Логирование других ошибок
            logger.info(f"Error sending message to {user_id}: {e}")
            failed += 1

    return successful, failed


def print_info_table(
    info_for_table: list[dict], header=list[str], ignore_field_names=list[str]
):
    table = PrettyTable()
    table.set_style(TableStyle.DOUBLE_BORDER)
    table.left_padding_width = 0
    table.right_padding_width = 0
    table.field_names = header

    for i in range(len(info_for_table)):
        filtered = {
            k: v for k, v in info_for_table[i].items() if k not in ignore_field_names
        }
        table.add_row(list(filtered.values()))

    return f"<pre>{table.get_string()}</pre>"


def parse_user_input_ids(ids: str) -> tuple[bool, list[int]]:
    """
    Parse and validate a comma-separated string of Telegram user IDs.

    Args:
        ids (str): A comma-separated string of Telegram user IDs

    Returns:
        tuple[bool, list[int]]: A tuple containing:
            - bool: True if the input is valid, False otherwise
            - list[int]: The list of parsed IDs if valid, empty list if invalid
    """
    # Check if input is a string
    if not isinstance(ids, str):
        return False, []

    # Remove any whitespace and check if the string is empty
    ids = ids.strip()
    if not ids:
        return False, []

    # Split by comma
    id_strings = ids.split(",")

    # Check if there's an empty element (happens with trailing comma)
    if any(not id_str.strip() for id_str in id_strings):
        return False, []

    try:
        # Try to convert each ID to an integer
        parsed_ids = [int(id_str.strip()) for id_str in id_strings]

        # Validate each ID (Telegram IDs are positive integers)
        for user_id in parsed_ids:
            # Check if IDs are valid Telegram user IDs (positive integers)
            if user_id <= 0:
                return False, []

            # Typically Telegram IDs are 9-10 digits long, but this is a soft check
            # as Telegram ID format might change in the future
            if len(str(user_id)) <= 6 or len(str(user_id)) >= 15:
                return False, []

        return True, parsed_ids
    except ValueError:
        # If any ID can't be converted to an integer
        return False, []
