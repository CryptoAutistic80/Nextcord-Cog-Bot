import nextcord
from nextcord.ext import commands

class Ping(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_ready(self):
    print("Ping is online and ready to pong!")

  @commands.command()
  async def ping(self, ctx):
    latency = round(self.bot.latency * 1000)
    
    # Create Embed object
    embed = nextcord.Embed(
        title="Pong!",
        description=f"Pong MFER! Oh and server ping is: {latency}ms....I think 😂",
        color=nextcord.Color.green()  # Or any color of your choice
    )
    await ctx.send(embed=embed)

def setup(bot):
  bot.add_cog(Ping(bot))

