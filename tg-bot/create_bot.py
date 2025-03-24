import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.client.session.aiohttp import AiohttpSession
from asyncpg_lite import DatabaseManager

ADMINS = [int(admin_id) for admin_id in os.environ.get("ADMINS").split(",")]
DATABASE_URL = os.environ.get("DATABASE_URL")
DEV_MODE = int(os.environ.get("DEV_MODE"))
USE_PROXY = int(os.environ.get("USE_PROXY"))
PROXY_URL = os.environ.get("PROXY_URL")
DEL_PASWD = os.environ.get("DEL_PASWD")
DEV_TOKEN = os.environ.get("DEV_TOKEN")
PROD_TOKEN = os.environ.get("PROD_TOKEN")
# PROD
TOKEN = PROD_TOKEN
session = None

if DEV_MODE:
    TOKEN = DEV_TOKEN

if USE_PROXY:
    session = AiohttpSession(proxy=PROXY_URL)


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
# DB
pg_manager = DatabaseManager(
    db_url=DATABASE_URL,
    deletion_password=DEL_PASWD,
    log_level="INFO",
    echo=False,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    session=session,
)
dp = Dispatcher(storage=MemoryStorage())
