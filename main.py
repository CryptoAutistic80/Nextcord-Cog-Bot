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


import asyncio  # Importing the asyncio library for asynchronous programming
import os  # Importing the os library for interacting with the operating system
import nextcord  # Importing the nextcord library, a Python wrapper for the Discord API
from nextcord.ext import commands  # Importing the commands extension from nextcord library
import keep_alive  # Importing the keep_alive module for keeping the bot alive
from modules.maintenance import Maintenance  # Importing the Maintenance class from the modules.maintenance module

# Creating an instance of the Intents class with all intents enabled
intents = nextcord.Intents.all()
intents.members = True

# Creating a new bot instance with a command prefix of '.' and the specified intents
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Retrieving the Discord token from the environment variable
discord_token = os.environ['DISCORD_TOKEN']

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

    Maintenance()  # Start the maintenance task

# Function to load all the cogs (modules) from the 'cogs' directory
def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')

# Asynchronous function that serves as the entry point for the bot
async def main():
    load()  # Load all the cogs
    await bot.start(discord_token)  # Start the bot with the specified token

# Call keep_alive function to keep the bot alive
keep_alive.keep_alive()

# Start the bot by running the main function using asyncio's run() method
asyncio.run(main())




