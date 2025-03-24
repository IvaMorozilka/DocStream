from aiogram import Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from keyboards.all_kb import main_kb
from aiogram.fsm.context import FSMContext
from db_handler.db_funk import get_user_info, get_request_info
from handlers.states import States

commands_router = Router()


@commands_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_info = await get_user_info(message.from_user.id)
    if user_info:
        await message.answer(
            text="Воспользуйтесь меню 📋",
            reply_markup=main_kb(),
        )
    else:
        user_info = await get_request_info(message.from_user.id)
        if user_info:
            status = user_info.get("status")
            if status == 0:
                await message.answer(
                    "Ваша заявка находиться на рассмотрении 🔎\nОжидайте уведомления."
                )
            elif status == 2:
                await message.answer("Ваша заявка была отклонена 😔")
        else:
            await message.answer(
                "Для начала вам стоит зарегистрироваться ✍\nПосле рассмотрения вашей заявки, вы сможете загружать данные для дашбордов."
            )
            await message.answer(
                "Отправьте свое полное ФИО, например: Иванов Иван Иванович"
            )
            await state.set_state(States.form_full_name)


@commands_router.message(Command("restart"))
async def restart_bot(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔄Состояние сброшено!", reply_markup=main_kb())
