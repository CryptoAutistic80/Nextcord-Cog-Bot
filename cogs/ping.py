import nextcord
from nextcord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ping Pong MFER")

    @nextcord.slash_command(description="Ping the bot, go on waste his time")
    async def ping(self, interaction: nextcord.Interaction):
        try:
            # Defer the response to buy more time
            await interaction.response.defer()
            
            latency = round(self.bot.latency * 1000)

            embed = nextcord.Embed(
                title="ALERT! Human wasting my time..",
                color=nextcord.Color.blue()
            )
            embed.add_field(name=" ", value=f"Pong MFER! oh and the latency is {latency}ms when I checked yesterday....", inline=False)

            await interaction.edit_original_message(embed=embed)

        except nextcord.NotFound as e:
            print(f"Error: Interaction not found ({interaction.id}): {e}")
            return

        except nextcord.HTTPException as e:
            print(f"HTTP error occurred when handling interaction ({interaction.id}): {e}")
            return

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            await interaction.send(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(Ping(bot))
