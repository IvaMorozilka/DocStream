from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    waiting_for_option = State()
    waiting_for_document = State()

    form_full_name = State()
    form_org_name = State()
    check_state = State()


class SettingsStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_ids = State()
