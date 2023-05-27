 # _____ _______     _______ _______ ____            _    _ _______ _____  _____ _______ _____ _____  
# / ____|  __ \ \   / /  __ \__   __/ __ \      /\  | |  | |__   __|_   _|/ ____|__   __|_   _/ ____| 
#| |    | |__) \ \_/ /| |__) | | | | |  | |    /  \ | |  | |  | |    | | | (___    | |    | || |      
#| |    |  _  / \   / |  ___/  | | | |  | |   / /\ \| |  | |  | |    | |  \___ \   | |    | || |      
#| |____| | \ \  | |  | |      | | | |__| |  / ____ \ |__| |  | |   _| |_ ____) |  | |   _| || |____  
# \_____|_|  \_\ |_|  |_|      |_|  \____/  /_/    \_\____/   |_|  |_____|_____/   |_|  |_____\_____| 
                                                                                                     
                                                                                                     
# ____  _            _        _           _         _____                       _                      
#|  _ \| |          | |      | |         (_)       |_   _|                     (_)                     
#| |_) | | ___   ___| | _____| |__   __ _ _ _ __     | |  _ __ ___   __ _  __ _ _ _ __   ___  ___ _ __ 
#|  _ <| |/ _ \ / __| |/ / __| '_ \ / _` | | '_ \    | | | '_ ` _ \ / _` |/ _` | | '_ \ / _ \/ _ \ '__|
#| |_) | | (_) | (__|   < (__| | | | (_| | | | | |  _| |_| | | | | | (_| | (_| | | | | |  __/  __/ |   
#|____/|_|\___/ \___|_|\_\___|_| |_|\__,_|_|_| |_| |_____|_| |_| |_|\__,_|\__, |_|_| |_|\___|\___|_|   
#                                                                          __/ |                       
#      James Walford 2023                                                 |___/
#      (Crypto Autistic)

import openai
import asyncio
import os
import nextcord
from nextcord.ext import commands
import keep_alive
import logging 

from cogs.chat import ChatCog 

class ExcludeSpecificLogFilter(logging.Filter):
    def filter(self, record):
        if record.name == 'nextcord.gateway' and 'heartbeat blocked' in record.getMessage():
            return False
        return True

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                    filename='bot.log')

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
f = ExcludeSpecificLogFilter()
logger.addFilter(f)

intents = nextcord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

discord_token = os.getenv('DISCORD_TOKEN')
openai.api_key = os.getenv('Key_OpenAI')

@bot.event
async def on_ready():
    logger.info(f'We have logged in as {bot.user}')

def load():
    chat_cog = ChatCog(bot)
    bot.chat_cog = chat_cog
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            if filename[:-3] == 'admin':
                bot.load_extension(f'cogs.{filename[:-3]}')
            else:
                bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    try:
        load()
        await bot.start(discord_token)
    finally:
        if 'chat_cog' in bot.__dict__:
            await bot.chat_cog.close()

keep_alive.keep_alive()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
