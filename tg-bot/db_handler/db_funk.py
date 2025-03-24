from create_bot import pg_manager
from sqlalchemy import BigInteger, Text, Boolean, DateTime, Integer


async def create_users_table():
    columns = [
        {
            "name": "user_id",
            "type": BigInteger,
            "options": {
                "primary_key": True,
                "unique": True,
            },
        },
        {
            "name": "username",
            "type": Text,
        },
        {
            "name": "full_name",
            "type": Text,
        },
        {
            "name": "org_name",
            "type": Text,
        },
        {"name": "admin", "type": Boolean},
    ]
    async with pg_manager:
        await pg_manager.create_table(table_name="users", columns=columns)


async def create_reg_requests_table():
    columns = [
        {
            "name": "user_id",
            "type": BigInteger,
            "options": {
                "primary_key": True,
                "unique": True,
            },
        },
        {
            "name": "username",
            "type": Text,
        },
        {
            "name": "full_name",
            "type": Text,
        },
        {
            "name": "org_name",
            "type": Text,
        },
        {"name": "admin", "type": Boolean},
        # 0 - pending, 1 - accepted, 2 - rejected
        {"name": "status", "type": Integer},
        {"name": "processed", "type": Boolean},
        {"name": "by_whom", "type": Text},
    ]
    async with pg_manager:
        await pg_manager.create_table(table_name="requests", columns=columns)


async def create_documents_table():
    columns = [
        {
            "name": "id",
            "type": BigInteger,
            "options": {
                "primary_key": True,
                "unique": True,
            },
        },
        {
            "name": "user_id",
            "type": BigInteger,
        },
        {
            "name": "filename",
            "type": Text,
        },
        {
            "name": "load_date",
            "type": DateTime,
        },
        {
            "name": "period",
            "type": Text,
        },
    ]
    async with pg_manager:
        await pg_manager.create_table(table_name="documnets", columns=columns)


async def get_user_info(user_id: int):
    async with pg_manager:
        user_info = await pg_manager.select_data(
            table_name="users",
            where_dict={"user_id": user_id},
            one_dict=True,
        )
        if user_info:
            return user_info
        else:
            return None


async def get_admins():
    async with pg_manager:
        admins_info = await pg_manager.select_data(
            table_name="users",
            where_dict={"admin": True},
        )
        return admins_info


async def get_all_users():
    async with pg_manager:
        users_info = await pg_manager.select_data(table_name="users")
        return users_info


async def get_recievers():
    async with pg_manager:
        recievers_info = await pg_manager.select_data(
            table_name="users",
            where_dict={"reciever": True},
        )
        return recievers_info


async def insert_user(user_data: dict):
    async with pg_manager:
        await pg_manager.insert_data_with_update(
            table_name="users", records_data=user_data, conflict_column="user_id"
        )


async def send_registration_request(user_data: dict):
    async with pg_manager:
        await pg_manager.insert_data_with_update(
            table_name="requests", records_data=user_data, conflict_column="user_id"
        )


async def get_request_info(user_id: int):
    async with pg_manager:
        request_info = await pg_manager.select_data(
            table_name="requests",
            where_dict={"user_id": user_id},
            one_dict=True,
        )
        if request_info:
            return request_info
        else:
            return None


async def process_request(user_id: int, status: int, by_whom: str):
    async with pg_manager:
        await pg_manager.update_data(
            table_name="requests",
            where_dict={"user_id": user_id},
            update_dict={"processed": True, "status": status, "by_whom": by_whom},
        )
        user_info = await get_request_info(user_id)
        return user_info
