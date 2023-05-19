import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
import openai
import os
import aiohttp
import io
from modules.image_process import stitch_images
from modules.buttons import ImageButton, RegenerateButton, VaryButton, RegenerateVaryButton


class ImageView(nextcord.ui.View):
    def __init__(self, image_paths, size, prompt, cog, button_type):
        super().__init__()
        for idx, image_path in enumerate(image_paths):
            image_button = ImageButton(label=f'I{idx+1}', image_path=image_path)
            image_button.row = 0
            self.add_item(image_button)

        if button_type == 'regenerate':
            regenerate_button = RegenerateButton(size, prompt, cog)
            regenerate_button.row = 0
            self.add_item(regenerate_button)
        elif button_type == 'regenerate_vary':
            regenerate_vary_button = RegenerateVaryButton(size, image_paths[0], cog)
            regenerate_vary_button.row = 0
            self.add_item(regenerate_vary_button)

        for idx, image_path in enumerate(image_paths):
            vary_button = VaryButton(label=f'V{idx+1}', image_path=image_path, size=size, cog=cog)
            vary_button.row = 1
            self.add_item(vary_button)


class Paint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Paintbrushes are live!")

    async def generate_image(self, interaction, user_prompt, size):
        if not interaction.response.is_done():
            await interaction.response.defer()

        size_str = size
        os.makedirs('new_images', exist_ok=True)

        openai.api_key = os.getenv('Key_OpenAI')

        response = openai.Image.create(
            prompt=user_prompt,
            n=4,
            size=size_str
        )

        file_to_send, image_files = stitch_images(response)

        with open(file_to_send, 'rb') as f:
            picture = nextcord.File(f)
            embed = nextcord.Embed(title="Your Picassimo!", color=nextcord.Color.yellow(), description=f"**Prompt:** {user_prompt}\n\n**Size:** {size}")
            embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")
            embed.set_image(url=f"attachment://{file_to_send}")

        view = ImageView(image_files, size, user_prompt, self, 'regenerate')
        await interaction.followup.send(embed=embed, file=picture, view=view)

        os.remove(file_to_send)

    async def vary_image(self, interaction, image_path, size):
        size_str = size
        os.makedirs('new_images', exist_ok=True)

        if not (image_path.startswith('http://') or image_path.startswith('https://')):
            with open(image_path, 'rb') as image_file:
                response = openai.Image.create_variation(
                    image=image_file,
                    n=4,
                    size=size_str
                )
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_path) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send('Could not download file...', ephemeral=True)
                    data = await resp.read()
                    byte_stream = io.BytesIO(data)
                    byte_array = byte_stream.getvalue()
                    response = openai.Image.create_variation(
                        image=byte_array,
                        n=4,
                        size=size_str
                    )

        file_to_send, image_files = stitch_images(response)

        with open(file_to_send, 'rb') as f:
            picture = nextcord.File(f)
            embed = nextcord.Embed(title="Your Picassimo Variations!", color=nextcord.Color.yellow(), description=f"**Size:** {size}")
            embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")
            embed.set_image(url=f"attachment://{file_to_send}")

        view = ImageView(image_files, size, None, self, 'regenerate_vary')
        await interaction.followup.send(embed=embed, file=picture, view=view)

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
        await self.generate_image(interaction, prompt, resolution)

def setup(bot):
    bot.add_cog(Paint(bot))
