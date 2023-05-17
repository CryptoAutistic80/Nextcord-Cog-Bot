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


import asyncio
import os
import nextcord
from nextcord.ext import commands
import keep_alive

intents = nextcord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

discord_token = os.environ['DISCORD_TOKEN']

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

def load():
  for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
      bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
  load()
  await bot.start(discord_token)

# Call keep_alive before starting your bot
keep_alive.keep_alive()

# Start your bot
asyncio.run(main())



