import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
import openai
import os
import aiohttp
import io
from modules.image_process import stitch_images

class ImageButton(nextcord.ui.Button):
    def __init__(self, label, image_path):
        super().__init__(label=label, style=nextcord.ButtonStyle.primary)
        self.image_path = image_path

    async def callback(self, interaction: nextcord.Interaction):
        with open(self.image_path, 'rb') as f:
            picture = nextcord.File(f)
            await interaction.response.send_message(file=picture, ephemeral=True)

class RegenerateButton(nextcord.ui.Button):
    def __init__(self, size, prompt, cog):
        super().__init__(style=nextcord.ButtonStyle.primary, label="🔄")
        self.size = size
        self.prompt = prompt
        self.cog = cog

    async def callback(self, interaction: nextcord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Trying again human...", ephemeral=True)
        await self.cog.generate_image(interaction, self.prompt, self.size)

class VaryButton(nextcord.ui.Button):
    def __init__(self, label, image_path, size, cog):
        super().__init__(label=label, style=nextcord.ButtonStyle.secondary)
        self.image_path = image_path
        self.size = size
        self.cog = cog

    async def callback(self, interaction: nextcord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("spinning some variety...", ephemeral=True)
        await self.cog.vary_image(interaction, self.image_path, self.size)

class ImageView(nextcord.ui.View):
    def __init__(self, image_paths, size, prompt, cog, include_RegenerateButton=False):
        super().__init__()
        for idx, image_path in enumerate(image_paths):
            image_button = ImageButton(label=f'I{idx+1}', image_path=image_path)
            image_button.row = 0
            self.add_item(image_button)

        if include_RegenerateButton:
            regenerate_button = RegenerateButton(size, prompt, cog)
            regenerate_button.row = 0
            self.add_item(regenerate_button)

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

        view = ImageView(image_files, size, user_prompt, self, include_RegenerateButton=True)
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

        view = ImageView(image_files, size, None, self, include_RegenerateButton=False)
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
