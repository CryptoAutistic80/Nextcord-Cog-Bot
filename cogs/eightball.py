import random
import json
import nextcord
import os
from nextcord.ext import commands
import openai  # Import the OpenAI API

class EightBall(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prompt = ""

        # Load prompt from the .json file
        with open('json/eightball_prompt.json', 'r') as file:
            self.prompt = json.load(file)['prompt']

        # Set the OpenAI API key from a Replit secret
        openai.api_key = os.getenv("Key_OpenAI")

    @commands.Cog.listener()
    async def on_ready(self):
        print("8 Ball ready!")

    @nextcord.slash_command(description="Ask the Magic 8-Ball a question")
    async def magic8ball(self, interaction: nextcord.Interaction, question: str):
        # Show that the bot is "thinking"
        await interaction.response.defer()

        # Generate a response using the GPT-3 model
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=self.prompt + question,
            max_tokens=60,
            temperature=0.8  # Set the temperature to 0.8
        ).choices[0].text.strip()

        # Create an embed to send as a response
        embed = nextcord.Embed(
            title="Magic 8-Ball",
            color=nextcord.Color.blue()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")

        # Send the embed as a response to the interaction
        await interaction.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(EightBall(bot))
