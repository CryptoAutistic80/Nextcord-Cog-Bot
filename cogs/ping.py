import nextcord  # Nextcord is a modern, feature-rich, easy-to-use, feature-rich, and async-ready API wrapper for Discord written in Python.
from nextcord.ext import commands  # This is a extension of nextcord for command handling.

class Ping(commands.Cog):  # A class named 'Ping' that inherits from the 'commands.Cog' class. This class represents a cog in the bot, which is a collection of commands and events.
    def __init__(self, bot):  # This is the constructor. The 'bot' argument is the instance of the bot that this cog belongs to.
        self.bot = bot  # This is the bot instance.

    @commands.Cog.listener()  # This is a decorator that declares a cog listener.
    async def on_ready(self):  # This function is called when the bot is ready.
        print("Ping Pong MFER")  # Prints a message to the console.

    @nextcord.slash_command(description="Ping the bot, go on waste his time")  # This decorator declares a slash command for pinging the bot.
    async def ping(self, interaction: nextcord.Interaction):  # The function that gets called when the '/ping' command is issued. The 'interaction' parameter is an instance of nextcord.Interaction.
        try:
            # Defer the response to buy more time
            await interaction.response.defer()  # Defer the interaction to allow for a later response.

            latency = round(self.bot.latency * 1000)  # Calculate the latency (in milliseconds) between the bot and the Discord server.

            embed = nextcord.Embed(  # Create an embed message.
                title="ALERT! Human wasting my time..",  # The title of the embed.
                color=nextcord.Color.blue()  # The color of the embed.
            )
            embed.add_field(name=" ", value=f"Pong MFER! oh and the latency is {latency}ms when I checked yesterday....", inline=False)  # Add a field to the embed.

            await interaction.edit_original_message(embed=embed)  # Edit the original interaction response with the embed message.

        except nextcord.NotFound as e:  # If the interaction is not found...
            print(f"Error: Interaction not found ({interaction.id}): {e}")  # Print an error message to the console.
            return

        except nextcord.HTTPException as e:  # If an HTTP error occurs when handling the interaction...
            print(f"HTTP error occurred when handling interaction ({interaction.id}): {e}")  # Print an error message to the console.
            return

        except Exception as e:  # If any other exception occurs...
            print(f"An unexpected error occurred: {e}")  # Print an error message to the console.
            await interaction.send(f"An error occurred: {e}")  # Send a message to the interaction channel about the error.

def setup(bot):
    bot.add_cog(Ping(bot))  # Add the 'Ping' cog to the bot.
