import io
import os
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ErrorEvent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.context import FSMContext

from keyboards.all_kb import main_kb
from keyboards.inline_kbs import goback_actions_kb, main_loader_kb
from utils.excel_helpers.checker import check_document_by_category
from utils.api import upload_documnet_to_filestoarage
from utils.helpers import send_document
from utils.constants import DASHBOARD_CALLBACKS, INSTRUCTIONS_IMAGES, DASHBOARD_NAMES
from handlers.states import States
from db_handler.db_funk import get_user_info

MINIO_UI_PATH = os.environ.get("MINIO_UI_PATH")

document_router = Router()


@document_router.callback_query(F.data.in_({"back"}))
async def process_change_mind(call: CallbackQuery, state: FSMContext):
    if call.data == "back":
        await call.message.edit_text(
            "Выберите дашборд, для которого вы хотите загрузить данные:",
            reply_markup=main_loader_kb(),
        )
        await call.answer()
        await state.set_state(States.waiting_for_option)


@document_router.message(~F.data, States.waiting_for_option)
async def process_option_choice(message: Message, state: FSMContext):  # noqa: F811
    await message.reply(text="⬆️Я жду, пока вы выберете дашборд")
    await state.update_data(States.waiting_for_option)


@document_router.callback_query(
    F.data.in_(DASHBOARD_CALLBACKS),
    States.waiting_for_option,
)
async def process_option_choice(call: CallbackQuery, state: FSMContext):  # noqa: F811
    option_name = call.data
    await state.update_data(option=option_name)

    if option_name != "ГуманитарнаяПомощьСВО":
        await call.answer("Доступен только Гуманитарная помощь СВО")
        return

    await call.answer()
    await call.message.edit_text(
        text=f"Выбран дашборд <b>{DASHBOARD_NAMES[option_name]}</b>.\n\nℹ Перед загрузкой рекомендую ознакомиться с инструкцией\n\nПрикрепите документ 🧷📄 в следующем сообщении ⬇️",
        reply_markup=goback_actions_kb(),
    )
    await state.set_state(States.waiting_for_document)


@document_router.callback_query(
    F.data.in_(DASHBOARD_CALLBACKS), States.waiting_for_document
)
async def process_option_choice(call: CallbackQuery, state: FSMContext):  # noqa: F811
    data = await state.get_data()
    option = data.get("option")
    await call.answer(f"Вы уже выбрали {option}. Жду от вас документа.")
    await state.set_state(States.waiting_for_document)


@document_router.message(~F.document, States.waiting_for_document)
async def process_document(message: Message, state: FSMContext):
    await message.reply("Это не похоже на документ. Повторите отправку.")
    await state.set_state(States.waiting_for_document)


@document_router.callback_query(F.data == "show_instruction")
async def send_instruction(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    option = data.get("option", "")
    if option:
        instr = FSInputFile(INSTRUCTIONS_IMAGES[option])
        await call.message.answer_photo(
            photo=instr, caption="Если возникли вопросы обратитесь к @azmsus"
        )
        await call.answer()
    else:
        await call.answer("Для показа инструкции нужно выбрать дашборд")


@document_router.message(F.document, States.waiting_for_document)
async def process_document(message: Message, state: FSMContext):  # noqa: F811
    data = await state.get_data()
    dshb_name = data.get("option")

    if not message.document.file_name.endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        await message.reply(
            "Пожалуйста, отправьте файл в формате таблиц Excel.\n\nℹ️ Поддерживаемые расширения файлов xlsx/xlsm/xltx/xltm"
        )
        return

    # Getting file info
    file_id = message.document.file_id
    file_name = message.document.file_name
    mime_type = message.document.mime_type

    # Downloading to bytes
    file_io = io.BytesIO()
    await message.bot.download(message.document, destination=file_io)
    file_io.seek(0)
    if not file_io:
        await message.answer("Не смог получить ваш файл, попробуйте отправить еще раз")
        return

    # Cheking + processing stage
    # 1 - Checking for correct headers
    result, errors = check_document_by_category(file_bytes=file_io, category=dshb_name)
    if not result:
        await message.answer(
            f"{errors}\n\nℹ️ Пожалуйста, отправьте новый документ следующим сообщением",
            reply_markup=(
                InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="📖 Посмотреть инструкцию",
                                callback_data="show_instruction",
                            ),
                            InlineKeyboardButton(
                                text="↩️ Вернуться к выбору", callback_data="back"
                            ),
                        ]
                    ]
                )
            ),
        )
        return
    # Loading to s3 store...
    error, response = await upload_documnet_to_filestoarage(
        file_io.getvalue(), file_name, mime_type, dshb_name
    )
    if error:
        await message.answer(f"Отправка в s3 не удалась {response}")
        return

    # Sending documnets with caption to admins ...
    inline_url = MINIO_UI_PATH + response.get("path")
    user_info = await get_user_info(message.from_user.id)
    caption_text = f"📄 Вам пришел новый документ!\n\n<b>Для дашборда:</b> {dshb_name}\n<b>Отправитель:</b> {user_info['full_name']}, @{message.from_user.username or 'не указан'}\n<b>Организация:</b> {user_info['org_name']}"
    total_users, users_ids_without_send = await send_document(
        file_id, message, caption_text, inline_url
    )
    user_names = ["Скоро будет. Пока неизвестно"]

    if len(users_ids_without_send) == total_users:
        await message.answer(
            "🔴При отправке документа произошла ошибка, документ не был отправлен.\nПопробуйте отправить документ еще раз. Если он так же не будет отправлен, обратитесь в поддержку."
        )
        return
    elif len(users_ids_without_send) != 0:
        await message.reply(
            f"🟡Документ был отправлен всем, кроме:\n({'\n'.join(user_names)})"
        )
        await state.clear()
    else:
        await message.reply(
            "🏁Ваш документ был успешно отправлен!",
            reply_markup=main_kb(),
        )
        await state.clear()

    await state.clear()


@document_router.error(
    ExceptionTypeFilter(TelegramBadRequest), F.update.message.as_("message")
)
async def handle_big_file_size(event: ErrorEvent, message: Message):
    if str(event.exception).endswith("file is too big"):
        await message.reply(
            "Размер вашего файла больше <b>20МБ</b> 👀. Это ограничение Telegram API. Жду документа меньшего размера.",
        )


# @document_router.message(F.document)
# async def handle_document(message: Message):
#     if not message.document.file_name.endswith((".xlsx")):
#         await message.answer("Пожалуйста, отправьте файл в формате Excel (.xlsx).")
#         return

#     async with ChatActionSender.upload_document(chat_id=message.chat.id, bot=bot):
#         await message.answer("Файл получен. Обрабатываю...")

#         # Downloading...
#         file_id = message.document.file_id
#         file = await bot.get_file(file_id)
#         file_path = file.file_path
#         file_name = message.document.file_name

#         downloaded_file = await bot.download_file(file_path)
#         os.makedirs(download_dir, exist_ok=True)
#         local_file_path = os.path.join(download_dir, f"{file_name}")
#         with open(local_file_path, "wb") as new_file:
#             new_file.write(downloaded_file.read())
#         # End download process

#         # Start processing...
#         processed_file_path = os.path.join(download_dir, f"ОБРАБОТАН_{file_name}")
#         code, msg, warnings, logs = transform_pipeline(
#             local_file_path, processed_file_path
#         )
#         # Errors handle
#         if not code:
#             await message.answer(f"❌ Произошла ошибка при обработке файла ❌\n{msg}")
#         else:
#             if len(warnings) != 0:
#                 await message.answer(
#                     f"⚠️<b>Внимание</b>⚠️\n{''.join(f'{idx}. {item}\n' for idx, item in enumerate(warnings))}"
#                 )
#                 await message.answer("🪵Логи вычислений🪵\n")
#                 await message.answer(
#                     "Расчет (РУБЛИ)\n"
#                     + "\n".join(
#                         f"{key}: <code>={value}</code>"
#                         for key, value in logs[0].items()
#                     )
#                 )
#                 await message.answer(
#                     "Расчет (ПРОЦЕНТЫ)\n"
#                     + "\n".join(
#                         f"{key}: <code>={value}</code>"
#                         for key, value in logs[1].items()
#                     )
#                 )
#             await message.answer("✅<b>Файл успешно обработан ✅</b>")
#             await message.reply_document(document=FSInputFile(processed_file_path))

#         # Удаляем временные файлы
#         os.remove(local_file_path)
#         os.remove(processed_file_path)
