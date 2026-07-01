import logging
import os
import bot
from dotenv import load_dotenv
from util.messagedata import MessageData, MessageDatabase

load_dotenv()

TOKEN = os.getenv('TOKEN')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logging.getLogger('disnake').setLevel(logging.WARNING)
logging.getLogger('logger.http').setLevel(logging.WARNING)

logger = logging.getLogger("envelope-bot")
logger.setLevel(logging.DEBUG)

logger.info("Started Envelope Bot")
database = MessageDatabase()
instance = bot.Bot(TOKEN, database)
