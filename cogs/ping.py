import nextcord  # Importing the nextcord library, a Python wrapper for the Discord API
from nextcord.ext import commands  # Importing the commands extension from nextcord library

# Defining a class named Ping that extends commands.Cog, representing the Ping functionality
class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Event listener decorator for the on_ready event
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ping is online and ready to pong!")

    # Slash command decorator for the ping command
    @nextcord.slash_command(description="Ping the bot, go on waste his time")
    async def ping(self, interaction: nextcord.Interaction):
        latency = round(self.bot.latency * 1000)  # Calculate the bot's latency in milliseconds

        # Create an embed to send as a response
        embed = nextcord.Embed(
            title="ALERT! Human wasting my time..",
            color=nextcord.Color.blue()
        )
        embed.add_field(name=" ", value=f"Pong MFER! oh and the latency is {latency}ms when I checked yesterday....", inline=False)

        await interaction.send(embed=embed)  # Send the embed as a response to the interaction

# Function to set up the Ping cog
def setup(bot):
    bot.add_cog(Ping(bot))


