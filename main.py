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



