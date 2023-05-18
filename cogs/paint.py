import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
import openai
import os
from modules.image_process import stitch_images

class ImageButton(nextcord.ui.Button):
    def __init__(self, label, image_path):
        super().__init__(label=label, style=nextcord.ButtonStyle.primary)
        self.image_path = image_path

    async def callback(self, interaction: nextcord.Interaction):
        with open(self.image_path, 'rb') as f:
            picture = nextcord.File(f)
            await interaction.response.send_message(file=picture, ephemeral=True)

class ImageView(nextcord.ui.View):
    def __init__(self, image_paths):
        super().__init__()
        for idx, image_path in enumerate(image_paths):
            self.add_item(ImageButton(label=f'V{idx+1}', image_path=image_path))

class Paint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Paintbrushes are live!")

    async def generate_image(self, interaction, user_prompt, size):
        # Defer the interaction
        await interaction.response.defer()

        size_str = size
        # Ensure that the 'new_images' directory exists
        os.makedirs('new_images', exist_ok=True)
    
        openai.api_key = os.getenv('Key_OpenAI')
    
        response = openai.Image.create(
            prompt=user_prompt,
            n=4,  # Always generate 4 images
            size=size_str  # Use the string version of the size
        )

        file_to_send, image_files = stitch_images(response)

        with open(file_to_send, 'rb') as f:
            picture = nextcord.File(f)
            embed = nextcord.Embed(title="Your Picassimo!", description=f"**Prompt:** {user_prompt}\n\n**Size:** {size}")
            embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")
            embed.set_image(url=f"attachment://{file_to_send}")

        view = ImageView(image_files)
        await interaction.followup.send(embed=embed, file=picture, view=view,)
  
        os.remove(file_to_send)

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
        # Call generate_image() directly
        await self.generate_image(interaction, prompt, resolution)

def setup(bot):
    bot.add_cog(Paint(bot))