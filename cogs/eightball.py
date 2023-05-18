import random
import json
import nextcord
from nextcord.ext import commands

class EightBall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.responses = []

        # Load responses from the .json file
        with open('json/responses.json', 'r') as file:
            self.responses = json.load(file)

    @commands.Cog.listener()
    async def on_ready(self):
        print("8 Ball ready!")

    @nextcord.slash_command(description="Ask the Magic 8-Ball a question")
    async def magic8ball(self, interaction: nextcord.Interaction, question: str):
        response = random.choice(self.responses)
        
        embed = nextcord.Embed(
            title="Magic 8-Ball",
            color=nextcord.Color.blue()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")
        
        await interaction.send(embed=embed)

def setup(bot):
    bot.add_cog(EightBall(bot))
