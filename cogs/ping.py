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

        embed = nextcord.Embed(
            title="The End is Nigh",
            color=nextcord.Color.blue()
        )
        embed.add_field(name=" ", value=f"Pong MFER! oh and the latency is {latency}ms when I checked yesterday....", inline=False)

        await interaction.send(embed=embed)
    
def setup(bot):
    bot.add_cog(Ping(bot))


