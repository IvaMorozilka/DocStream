from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from handlers.states import States

from keyboards.inline_kbs import main_loader_kb, generate_settings_kb
from keyboards.all_kb import main_kb
from db_handler.db_funk import get_user_info, get_admins


menu_router = Router()


@menu_router.message(F.text == "⬇️Загрузить данные")
async def show_upload_options(message: Message, state: FSMContext):
    await state.clear()
    user_info = await get_user_info(message.from_user.id)
    if user_info:
        await message.answer(
            "Выберите дашборд, для которого вы хотите загрузить данные:",
            reply_markup=main_loader_kb(),
        )
        await state.set_state(States.waiting_for_option)
    else:
        await message.answer(
            "Для начала загрузки вам нужно представиться. Воспользуйтесь командой /start"
        )


@menu_router.message(F.text == "🛟Поддержка")
async def show_support_options(message: Message):
    await message.answer(
        text="🐞Если у вас возникли трудности с работой бота:\n👉🏾Вы не можете загрузить документ\n👉🏾У вас проблема с навигацией по меню\n👉🏾Возникла ошибка при работе бота\n💬Для начала попробуйте перезапустить бота, командой /restart.\nЕсли это не помогло, напишите разработчику @Bobflipflop\n\n❓Если у вас возникли вопросы, по поводу загружаемых данных напишите свой вопрос - @mkuzhlev",
        reply_markup=main_kb(),
    )


@menu_router.message(F.text == "⚙️Настройки")
async def show_settings(message: Message):
    admins = await get_admins()
    if any(message.from_user.id in admin.values() for admin in admins):
        await message.answer(
            text="Главное меню",
            reply_markup=generate_settings_kb("main"),
        )
    else:
        await message.answer("Только для администраторов 👨🏻‍💼")
