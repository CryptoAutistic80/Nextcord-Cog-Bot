import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
import openai
import os
from modules.image_process import stitch_images

class Paint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Paintbrushes are live!")

    @nextcord.slash_command(description="Generate an image from a text prompt")
    async def paint(self, 
                    interaction: nextcord.Interaction, 
                    prompt: str,
                    resolution: str = SlashOption(
                        choices={
                            "256x256": "256x256", 
                            "512x512": "512x512", 
                            "1024x1024": "1024x1024"
                        },
                        description="Choose the resolution for the image"
                    )):
        # Defer the response
        await interaction.response.defer()

        openai.api_key = os.getenv('Key_OpenAI')
        response = openai.Image.create(
            prompt=prompt,
            n=4,  # Always generate 4 images
            size=resolution
        )

        # Stitch the images into a 2x2 collage
        collage_file, _ = stitch_images(response)

        # Create an embed message with the collage image
        embed = nextcord.Embed(
            title="Generated Images",
            color=nextcord.Color.blue()
        )
        embed.set_image(url=f"attachment://{collage_file}")

        # Send the embed message with the collage image
        with open(collage_file, 'rb') as f:
            file = nextcord.File(f)
            await interaction.edit_original_message(embed=embed, file=file)

def setup(bot):
    bot.add_cog(Paint(bot))


