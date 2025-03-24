from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from datetime import datetime, timezone, timedelta


from keyboards.all_kb import main_kb
from keyboards.inline_kbs import register_request_kb
from aiogram.fsm.context import FSMContext
from db_handler.db_funk import (
    get_user_info,
    insert_user,
    get_admins,
    process_request,
    send_registration_request,
    get_request_info,
)
from handlers.states import States
from create_bot import ADMINS, bot
from utils.checkers import check_full_name, check_org_name
from utils.constants import RegistrationCallback


reg_router = Router()


@reg_router.message(F.text, States.form_full_name)
async def capture_fullname(message: Message, state: FSMContext):
    if not check_full_name(message.text):
        await message.reply(
            text="ФИО неверно, повторите отправку.\n• Фамилия, имя и отчество должны начинаться с заглавной буквы.\n• Используйте только русские буквы.\n• Между словами должен быть один пробел."
        )
        await state.set_state(States.form_full_name)
        return

    await state.update_data(
        {
            "full_name": message.text,
            "user_id": message.from_user.id,
            "username": f"@{message.from_user.username if message.from_user.username else 'не_указан'}",
        }
    )
    await message.answer(f"{message.text}, из какой вы организации?")
    await state.set_state(States.form_org_name)


@reg_router.message(F.text, States.form_org_name)
async def capture_orgname(message: Message, state: FSMContext):
    if not check_org_name(message.text):
        await message.reply(
            text="Название организации неверно, повторите отправку. Пожалуйста, используйте только следующие символы:\n• Русские буквы в любом регистре\n• Цифры\n• Пробелы\n• Одинарные и двойные кавычки (' и \")\n• Тире (-)\n• Елочки (« и »)"
        )
        await state.set_state(States.form_org_name)
        return
    await state.update_data(org_name=message.text)
    data = await state.get_data()
    await message.answer(
        f"Проверьте свои данные:\n\n<b>ФИО</b>: {data.get('full_name')}\n<b>Огранизация</b>: {data.get('org_name')}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Отправить запрос", callback_data="correct"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Заполнить сначала",
                        callback_data="incorrect",
                    )
                ],
            ]
        ),
    )
    await state.set_state(States.check_state)


@reg_router.callback_query(F.data == "correct", States.check_state)
async def finish_form(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    if call.from_user.id in ADMINS:
        await insert_user({**data, "admin": True})
        await call.message.edit_text(
            "Регистрация успешна. Вы были указаны в списке Администраторов 👨🏻‍💻"
        )
    else:
        await send_registration_request(
            {**data, "admin": False, "processed": False, "status": 0}
        )
        await call.message.edit_text(
            text="Ваш запрос был направлен Администраторам 📨 Ожидайте уведомления с решением.",
            reply_markup=None,
        )
        admins_info = await get_admins()
        for user_id in [admin["user_id"] for admin in admins_info]:
            await bot.send_message(
                chat_id=user_id,
                text=f"<b>Новый запрос на регистрацию</b> 🙋‍♂️\n\nДата и время: {datetime.now(timezone(timedelta(hours=3))).strftime('%d-%m-%y %H:%M')}\nИмя: {data.get('full_name')}, {data.get('username')}\nОрганизация: {data.get('org_name')}",
                reply_markup=register_request_kb(data.get("user_id")),
            )
    await state.clear()


@reg_router.callback_query(F.data == "incorrect", States.check_state)
async def finish_form(call: CallbackQuery, state: FSMContext):  # noqa: F811
    await call.answer()
    await call.message.answer("Хорошо, давайте начнем заново.")
    await call.message.answer(
        "Отправьте свое полное ФИО, например: Иванов Иван Иванович"
    )
    await state.set_state(States.form_full_name)


@reg_router.callback_query(RegistrationCallback.filter(F.action == "a"))
async def accept_registration(call: CallbackQuery, callback_data: RegistrationCallback):
    request_info = await get_request_info(user_id=callback_data.user_id)

    if request_info.get("processed"):
        await call.message.edit_text(
            f"👨🏻‍💻 {request_info.get('by_whom')} уже принял данную заявку ✅"
        )
        return
    # Делаем вставку без status и processed
    await insert_user(
        {
            k: v
            for k, v in request_info.items()
            if k not in {"status", "processed", "by_whom"}
        }
    )
    admin_info = await get_user_info(call.from_user.id)
    await process_request(
        request_info.get("user_id"),
        status=1,
        by_whom=f"{admin_info.get('full_name')}, {admin_info.get('username')}",
    )
    await call.message.edit_text(
        f"Пользователь {request_info.get('full_name')}, {request_info.get('username')} принят ✅"
    )

    await bot.send_message(
        chat_id=callback_data.user_id,
        text="Ваш запрос был принят 🥳. Теперь вы можете загружать данные.",
        reply_markup=main_kb(),
    )


@reg_router.callback_query(RegistrationCallback.filter(F.action == "r"))
async def reject_registration(call: CallbackQuery, callback_data: RegistrationCallback):
    request_info = await get_request_info(user_id=callback_data.user_id)

    if request_info.get("processed"):
        await call.message.edit_text(
            f"👨🏻‍💻 {request_info.get('by_whom')} уже отклонил данную заявку ⛔"
        )
        return

    await call.message.edit_text(
        f"Пользователь {request_info.get('full_name')}, {request_info.get('username')} отклонен ⛔"
    )
    admin_info = await get_user_info(call.from_user.id)
    await process_request(
        request_info.get("user_id"),
        status=2,
        by_whom=f"{admin_info.get('full_name')}, {admin_info.get('username')}",
    )
    await bot.send_message(
        chat_id=callback_data.user_id,
        text="Ваш запрос был отклонен 😔",
        reply_markup=main_kb(),
    )
