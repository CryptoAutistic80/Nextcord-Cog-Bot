import random  # Importing the random module for generating random choices
import json  # Importing the json module for working with JSON data
import nextcord  # Importing the nextcord library, a Python wrapper for the Discord API
from nextcord.ext import commands  # Importing the commands extension from nextcord library

# Defining a class named EightBall that extends commands.Cog, representing the Magic 8-Ball functionality
class EightBall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.responses = []

        # Load responses from the .json file
        with open('json/responses.json', 'r') as file:
            self.responses = json.load(file)

    # Event listener decorator for the on_ready event
    @commands.Cog.listener()
    async def on_ready(self):
        print("8 Ball ready!")

    # Slash command decorator for the magic8ball command
    @nextcord.slash_command(description="Ask the Magic 8-Ball a question")
    async def magic8ball(self, interaction: nextcord.Interaction, question: str):
        response = random.choice(self.responses)  # Select a random response from the list of responses

        # Create an embed to send as a response
        embed = nextcord.Embed(
            title="Magic 8-Ball",
            color=nextcord.Color.blue()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")

        # Send the embed as a response to the interaction
        await interaction.send(embed=embed)

# Function to set up the EightBall cog
def setup(bot):
    bot.add_cog(EightBall(bot))