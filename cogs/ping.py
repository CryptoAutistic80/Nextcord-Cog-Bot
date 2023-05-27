import nextcord
import logging
from nextcord.ext import commands

# Set up logging
logger = logging.getLogger('discord')

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Ping is online and ready to pong!")
        print("Ping Pong MFER")

    @nextcord.slash_command(description="Ping the bot, go on waste his time")
    async def ping(self, interaction: nextcord.Interaction):
        try:
            # Defer the response to buy more time
            await interaction.response.defer()
            
            latency = round(self.bot.latency * 1000)
            logger.info(f'Bot latency: {latency}ms')

            embed = nextcord.Embed(
                title="ALERT! Human wasting my time..",
                color=nextcord.Color.blue()
            )
            embed.add_field(name=" ", value=f"Pong MFER! oh and the latency is {latency}ms when I checked yesterday....", inline=False)

            await interaction.edit_original_message(embed=embed)

        except nextcord.NotFound as e:
            logger.error(f"Error: Interaction not found ({interaction.id}): {e}")
            return

        except nextcord.HTTPException as e:
            logger.error(f"HTTP error occurred when handling interaction ({interaction.id}): {e}")
            return

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            await interaction.send(f"An error occurred: {e}")

def setup(bot):
    bot.add_cog(Ping(bot))
