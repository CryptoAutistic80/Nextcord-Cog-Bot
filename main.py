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

import os
import logging
import threading
from threading import Thread, active_count
from cogs.chat import ChatCog
import openai
import asyncio
import nextcord
from nextcord.ext import commands
import time

os.environ['PYTHONASYNCIODEBUG'] = '1'

# Configure the logging
with open('discord.log', 'w'):
    pass

logging.basicConfig(filename='discord.log', level=logging.INFO)

intents = nextcord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

discord_token = os.getenv('DISCORD_TOKEN')
openai.api_key = os.getenv('Key_OpenAI')

class Worker:
    def __init__(self, bot, max_tasks: int):
        self.bot = bot
        self.semaphore = asyncio.Semaphore(max_tasks)
        self.loop = asyncio.get_event_loop()

    async def task(self):
        async with self.semaphore:
            await self.bot.start(discord_token)

    def add_task(self):
        asyncio.run_coroutine_threadsafe(self.task(), self.loop)

@bot.event
async def on_ready():
    logging.info('Bot has connected to Discord!')
    print('Bot has connected to Discord!')

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
        worker = Worker(bot, 5)  # set max_tasks to be equal to the maximum amount of shards you'll use
        await worker.task()  # This line was modified.
    finally:
        if 'chat_cog' in bot.__dict__:
            await bot.chat_cog.close()

known_threads = set()

def manage_threads():
    while True:
        current_threads = set(threading.enumerate())
        new_threads = current_threads - known_threads
        closed_threads = known_threads - current_threads
        
        for thread in new_threads:
            logging.info(f"Thread created: {thread.name}")
        
        for thread in closed_threads:
            logging.info(f"Thread closed: {thread.name}")
        
        known_threads.update(new_threads)
        
        print(f"Currently active threads: {active_count()}")
        time.sleep(10)  # check every 10 seconds

Thread(target=manage_threads, name="Thread Management").start()

def discord_log_filter(record):
    log_message = record.getMessage()
    if log_message.startswith("WARNING:nextcord.gateway:Shard ID None heartbeat blocked for more than 10 seconds."):
        log_message = "WARNING:nextcord.gateway:Shard ID None heartbeat blocked for more than 10 seconds. Loop thread traceback (most recent call last): asyncio issue"
    return log_message

logging.getLogger().addFilter(discord_log_filter)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        asyncio.ensure_future(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
