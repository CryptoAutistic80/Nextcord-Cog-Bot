# Import necessary modules
import nextcord  # Library for building Discord bots
from nextcord.ext import commands  # Additional classes for command handling
from nextcord import SlashOption  # Specific class for creating slash command options
import openai  # OpenAI's Python library, used to interact with the GPT-3 API
import os  # OS module for operating system-related operations
import aiohttp  # Asynchronous HTTP client/server for asyncio
import asyncio  # Library for writing single-threaded concurrent code
import io  # Module provides capability to handle the IO operations
from modules.image_process import stitch_images, process_image  # Custom functions for processing images
from modules.buttons import ImageButton, RegenerateButton, VaryButton, RegenerateVaryButton  # Custom classes for interactive buttons

# 'ImageView' class is a child class of 'nextcord.ui.View'. It's used to create the UI for the bot.
class ImageView(nextcord.ui.View):
    def __init__(self, image_paths, size, prompt, cog, button_type):
        super().__init__()  # Call the constructor of the parent class

        # Add image buttons for each generated image
        for idx, image_path in enumerate(image_paths):
            image_button = ImageButton(label=f'I{idx+1}', image_path=image_path)
            image_button.row = 0
            self.add_item(image_button)

        # Add a regenerate button or a regenerate-vary button based on 'button_type'
        if button_type == 'regenerate':
            regenerate_button = RegenerateButton(size, prompt, cog)
            regenerate_button.row = 0
            self.add_item(regenerate_button)
        elif button_type == 'regenerate_vary':
            regenerate_vary_button = RegenerateVaryButton(size, image_paths[0], cog)
            regenerate_vary_button.row = 0
            self.add_item(regenerate_vary_button)

        # Add vary buttons for each generated image
        for idx, image_path in enumerate(image_paths):
            vary_button = VaryButton(label=f'V{idx+1}', image_path=image_path, size=size, cog=cog)
            vary_button.row = 1
            self.add_item(vary_button)

# 'Worker' class is used to manage bot tasks like creating images or variations
class Worker:
    def __init__(self, cog):
        self.cog = cog
        self.semaphore = asyncio.Semaphore(5)  # Limit the number of concurrent tasks

    # Method for creating images. If it fails, it tries again up to 3 times
    async def create_image(self, prompt, size, n):
        async with self.semaphore:
            for attempt in range(3):
                try:
                    response = await asyncio.to_thread(
                        openai.Image.create,
                        prompt=prompt,
                        n=n,
                        size=size
                    )
                    return response
                except Exception:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1)

    # Method for creating image variations. If it fails, it tries again up to 3 times
    async def create_image_variation(self, image, size, n):
        async with self.semaphore:
            for attempt in range(3):
                try:
                    response = await asyncio.to_thread(
                        openai.Image.create_variation,
                        image=image,
                        n=n,
                        size=size
                    )
                    return response
                except Exception:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1)

# 'Paint' class is a cog containing commands and listeners for the bot
class Paint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.worker = Worker(self)

    @commands.Cog.listener()  # Listener decorator to create event listeners
    async def on_ready(self):
        print("Paints mixed")  # Output when the bot is ready

    # Command to generate an image from a user prompt and send it in the Discord chat
    async def generate_image(self, interaction, user_prompt, size):
        # If the interaction response is not completed, defer it
        if not interaction.response.is_done():
            await interaction.response.defer()

        # Create the necessary directories
        os.makedirs('ai_resources/new_images', exist_ok=True)

        # Create images and stitch them together
        response = await self.worker.create_image(user_prompt, size, 4)
        file_to_send, image_files = await asyncio.to_thread(stitch_images, response)

        # Send the image with an embed and the ImageView
        with open(file_to_send, 'rb') as f:
            picture = nextcord.File(f)
            embed = nextcord.Embed(title="Your Picassimo!", color=nextcord.Color.yellow(),
                                  description=f"**Prompt:** {user_prompt}\n\n**Size:** {size}")
            embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")
            embed.set_image(url=f"attachment://{file_to_send}")

        view = ImageView(image_files, size, user_prompt, self, 'regenerate')
        await interaction.followup.send(embed=embed, file=picture, view=view)

        # Remove the sent file
        await asyncio.to_thread(os.remove, file_to_send)

    # Command to generate variations of an image and send them in the Discord chat
    async def vary_image(self, interaction, image_path, size):
        # Create the necessary directories
        os.makedirs('ai_resources/new_images', exist_ok=True)

        # Generate variations of the image and stitch them together
        if not (image_path.startswith('http://') or image_path.startswith('https://')):
            with open(image_path, 'rb') as image_file:
                response = await self.worker.create_image_variation(image_file, size, 4)
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_path) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send('Could not download file...', ephemeral=True)
                    data = await resp.read()
                    byte_stream = io.BytesIO(data)
                    byte_array = byte_stream.getvalue()
                    response = await self.worker.create_image_variation(byte_array, size, 4)

        file_to_send, image_files = await asyncio.to_thread(stitch_images, response)

        # Send the image variations with an embed and the ImageView
        with open(file_to_send, 'rb') as f:
            picture = nextcord.File(f)
            embed = nextcord.Embed(title="Your Picassimo Variations!", color=nextcord.Color.yellow(),
                                  description=f"**Size:** {size}")
            embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")
            embed.set_image(url=f"attachment://{file_to_send}")

        view = ImageView(image_files, size, None, self, 'regenerate_vary')
        await interaction.followup.send(embed=embed, file=picture, view=view)

        # Remove the sent file
        await asyncio.to_thread(os.remove, file_to_send)

    # Slash command to generate an image from a user prompt
    @nextcord.slash_command(description="Generate an image from a text prompt")
    async def paint(self, interaction: nextcord.Interaction, prompt: str,
                    resolution: str = SlashOption(
                        choices={"256x256": "256x256", "512x512": "512x512", "1024x1024": "1024x1024"},
                        description="Choose the resolution for the image"
                    )):
        await self.generate_image(interaction, prompt, resolution)

    # Slash command to generate variations of a user-uploaded image
    @nextcord.slash_command(description="Upload an image and generate variations")
    async def upload(self, interaction: nextcord.Interaction,
                     resolution: str = SlashOption(
                         choices={"256x256": "256x256", "512x512": "512x512", "1024x1024": "1024x1024"},
                         description="Choose the output resolution"
                     )):
        try:
            await interaction.response.defer()

            # Search the channel history for an image uploaded by the user
            messages = await interaction.channel.history(limit=50).flatten()
            image_url = None
            for message in messages:
                if message.author == interaction.user and message.attachments:
                    image_url = message.attachments[0].url
                    break

            # Process the found image and generate variations
            if image_url:
                file_name = "ai_resources/new_images/uploaded_image.png"
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status != 200:
                            return await interaction.response.send_message("Could not download file...",
                                                                           ephemeral=True)
                        data = await resp.read()
                        with open(file_name, 'wb') as f:
                            f.write(data)

                processed_image_path = process_image(file_name)
                await self.vary_image(interaction, processed_image_path, resolution)
            else:
                await interaction.response.send_message("Please upload an image.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

# Function to set up the bot
def setup(bot):
    bot.add_cog(Paint(bot))  # Add the Paint cog to the bot
