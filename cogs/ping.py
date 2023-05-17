import nextcord
from nextcord.ext import commands

class Ping(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_ready(self):
    print("Ping is online and ready to pong!")

  @nextcord.slash_command(description="Ping the bot, go on waste his time")
  async def ping(self, interaction : nextcord.Interaction):
    latency = round(self.bot.latency * 1000)

    await interaction.send(f"Pong MFER! Oh and server ping is: {latency}ms....I think 😂")
    
def setup(bot):
  bot.add_cog(Ping(bot))

