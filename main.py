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

# Import necessary modules
import os                          # Module for interacting with the operating system
import logging                     # Module for logging events
import threading                   # Module for working with threads
from threading import Thread, active_count  # Specific classes and functions from the threading module
from cogs.chat import ChatCog      # Import a custom module 'ChatCog' from the 'cogs' package
import openai                     # Module for interacting with the OpenAI API
import asyncio                    # Module for asynchronous programming
import nextcord                   # Module for creating Discord bots
from nextcord.ext import commands  # Specific class from the nextcord module
import time                       # Module for time-related functions

# Set an environment variable to enable debugging of asyncio
os.environ['PYTHONASYNCIODEBUG'] = '1'

# Configure the logging
with open('discord.log', 'w'):
    pass

logging.basicConfig(filename='discord.log', level=logging.INFO)  # Configure logging to write to 'discord.log' file

# Configure Discord bot intents
intents = nextcord.Intents.all()
intents.members = True

# Create a Discord bot instance
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Get Discord token and OpenAI API key from environment variables
discord_token = os.getenv('DISCORD_TOKEN')
openai.api_key = os.getenv('Key_OpenAI')

# Define a class 'Worker' for managing bot tasks
class Worker:
    def __init__(self, bot, max_tasks: int):
        self.bot = bot
        self.semaphore = asyncio.Semaphore(max_tasks)  # Limit the number of tasks that can be executed simultaneously
        self.loop = asyncio.get_event_loop()            # Get the event loop for the current thread

    async def task(self):
        async with self.semaphore:
            await self.bot.start(discord_token)   # Start the Discord bot

    def add_task(self):
        asyncio.run_coroutine_threadsafe(self.task(), self.loop)  # Schedule a task on the event loop

# Define an event handler for when the bot is ready
@bot.event
async def on_ready():
    logging.info('Bot has connected to Discord!')  # Log a message
    print('Bot has connected to Discord!')        # Print a message

# Define a function to load bot commands and extensions
def load():
    chat_cog = ChatCog(bot)  # Create an instance of the 'ChatCog' class
    bot.chat_cog = chat_cog  # Store the instance in the bot object
    for filename in os.listdir('./cogs'):     # Iterate over files in the 'cogs' directory
        if filename.endswith('.py'):          # Check if the file has a '.py' extension
            if filename[:-3] == 'admin':      # Check if the file name without the extension is 'admin'
                bot.load_extension(f'cogs.{filename[:-3]}')  # Load the extension
            else:
                bot.load_extension(f'cogs.{filename[:-3]}')  # Load the extension

# Define an async function 'main' to perform the main tasks
async def main():
    try:
        load()                                 # Load bot commands and extensions
        worker = Worker(bot, 5)                # Create an instance of the 'Worker' class with max_tasks set to 5
        await worker.task()                    # Execute the bot's task asynchronously
    finally:
        if 'chat_cog' in bot.__dict__:
            await bot.chat_cog.close()          # Close the chat_cog if it exists

known_threads = set()  # Create an empty set to keep track of known threads

# Define a function 'manage_threads' to manage threads
def manage_threads():
    while True:
        current_threads = set(threading.enumerate())  # Get the set of currently active threads
        new_threads = current_threads - known_threads  # Get the threads that are newly created
        closed_threads = known_threads - current_threads  # Get the threads that are closed

        for thread in new_threads:
            logging.info(f"Thread created: {thread.name}")  # Log the newly created threads

        for thread in closed_threads:
            logging.info(f"Thread closed: {thread.name}")  # Log the closed threads

        known_threads.update(new_threads)  # Update the known_threads set with the new threads

        print(f"Currently active threads: {active_count()}")  # Print the number of active threads
        time.sleep(10)  # Wait for 10 seconds before checking again

Thread(target=manage_threads, name="Thread Management").start()  # Start a thread to manage other threads

# Define a function to filter Discord log messages
def discord_log_filter(record):
    log_message = record.getMessage()
    if log_message.startswith("WARNING:nextcord.gateway:Shard ID None heartbeat blocked for more than 10 seconds."):
        log_message = "WARNING:nextcord.gateway:Shard ID None heartbeat blocked for more than 10 seconds. Loop thread traceback (most recent call last): asyncio issue"
    return log_message

# Add the log filter to the root logger
logging.getLogger().addFilter(discord_log_filter)

# Entry point of the program
if __name__ == "__main__":
    loop = asyncio.get_event_loop()  # Get the event loop
    try:
        asyncio.ensure_future(main())  # Schedule the 'main' function as a future task
        loop.run_forever()             # Run the event loop indefinitely
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())  # Shut down the event loop
        loop.close()                                         # Close the event loop


 