import nextcord  # Importing the nextcord library, a Python wrapper for the Discord API
from nextcord.ext import commands  # Importing the commands extension from nextcord library
from nextcord import SlashOption  # Importing the SlashOption class from nextcord
import openai  # Importing the openai library for working with OpenAI's API
import os  # Importing the os library for interacting with the operating system
import aiohttp  # Importing the aiohttp library for making asynchronous HTTP requests
import io  # Importing the io module for working with streams
from modules.image_process import stitch_images, process_image  # Importing the stitch_images function from the modules.image_process module
from modules.buttons import ImageButton, RegenerateButton, VaryButton, RegenerateVaryButton  # Importing custom button classes from the modules.buttons module

# Defining a class named ImageView that extends nextcord.ui.View, representing a view for displaying images with buttons
class ImageView(nextcord.ui.View):
    def __init__(self, image_paths, size, prompt, cog, button_type):
        super().__init__()

        # Create ImageButton instances for each image path and add them to the view
        for idx, image_path in enumerate(image_paths):
            image_button = ImageButton(label=f'I{idx+1}', image_path=image_path)
            image_button.row = 0
            self.add_item(image_button)

        # Add a regenerate button or regenerate-vary button based on the button type
        if button_type == 'regenerate':
            regenerate_button = RegenerateButton(size, prompt, cog)
            regenerate_button.row = 0
            self.add_item(regenerate_button)
        elif button_type == 'regenerate_vary':
            regenerate_vary_button = RegenerateVaryButton(size, image_paths[0], cog)
            regenerate_vary_button.row = 0
            self.add_item(regenerate_vary_button)

        # Create VaryButton instances for each image path and add them to the view
        for idx, image_path in enumerate(image_paths):
            vary_button = VaryButton(label=f'V{idx+1}', image_path=image_path, size=size, cog=cog)
            vary_button.row = 1
            self.add_item(vary_button)

# Defining a class named Paint that extends commands.Cog, representing the Paint functionality
class Paint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Event listener decorator for the on_ready event
    @commands.Cog.listener()
    async def on_ready(self):
        print("Paintbrushes are live!")

    # Asynchronous method for generating an image based on user prompt and size
    async def generate_image(self, interaction, user_prompt, size):
        if not interaction.response.is_done():
            await interaction.response.defer()

        size_str = size
        os.makedirs('ai_resources/new_images', exist_ok=True)

        # Set the OpenAI API key
        openai.api_key = os.getenv('Key_OpenAI')

        # Create an image using OpenAI's API based on the user prompt and specified size
        response = openai.Image.create(
            prompt=user_prompt,
            n=4,
            size=size_str
        )

        file_to_send, image_files = stitch_images(response)  # Stitch the generated images together

        # Create an embed to send as a response
        with open(file_to_send, 'rb') as f:
            picture = nextcord.File(f)
            embed = nextcord.Embed(title="Your Picassimo!", color=nextcord.Color.yellow(), description=f"**Prompt:** {user_prompt}\n\n**Size:** {size}")
            embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")
            embed.set_image(url=f"attachment://{file_to_send}")

        view = ImageView(image_files, size, user_prompt, self, 'regenerate')  # Create an instance of ImageView with the image files
        await interaction.followup.send(embed=embed, file=picture, view=view)  # Send the embed and image as a response to the interaction

        os.remove(file_to_send)  # Remove the temporary stitched image file

    # Asynchronous method for varying an image based on the image path and size
    async def vary_image(self, interaction, image_path, size):
        size_str = size
        os.makedirs('ai_resources/new_images', exist_ok=True)

        # If the image path is a local file
        if not (image_path.startswith('http://') or image_path.startswith('https://')):
            with open(image_path, 'rb') as image_file:
                response = openai.Image.create_variation(
                    image=image_file,
                    n=4,
                    size=size_str
                )
        else:  # If the image path is a URL
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

        file_to_send, image_files = stitch_images(response)  # Stitch the varied images together

        # Create an embed to send as a response
        with open(file_to_send, 'rb') as f:
            picture = nextcord.File(f)
            embed = nextcord.Embed(title="Your Picassimo Variations!", color=nextcord.Color.yellow(), description=f"**Size:** {size}")
            embed.set_thumbnail(url="https://gateway.ipfs.io/ipfs/QmeQZvBhbZ1umA4muDzUGfLNQfnJmmTVsW3uRGJSXxXWXK")
            embed.set_image(url=f"attachment://{file_to_send}")

        view = ImageView(image_files, size, None, self, 'regenerate_vary')  # Create an instance of ImageView with the image files
        await interaction.followup.send(embed=embed, file=picture, view=view)  # Send the embed and image as a response to the interaction

        os.remove(file_to_send)  # Remove the temporary stitched image file

    # Slash command decorator for the paint command
    @nextcord.slash_command(description="Generate an image from a text prompt")
    async def paint(self, interaction: nextcord.Interaction, prompt: str,
                    resolution: str = SlashOption(
                        choices={"256x256": "256x256", "512x512": "512x512", "1024x1024": "1024x1024"},
                        description="Choose the resolution for the image"
                    )):
        await self.generate_image(interaction, prompt, resolution)  # Generate and send the image based on the user prompt and resolution

    @nextcord.slash_command(description="Upload an image and generate variations")
    async def upload(self, interaction: nextcord.Interaction,
                     resolution: str = SlashOption(
                         choices={"256x256": "256x256", "512x512": "512x512", "1024x1024": "1024x1024"},
                         description="Choose the resolution for the image"
                     )):
    
        # Defer the interaction
        await interaction.response.defer()
    
        # Fetch recent messages in the channel
        messages = await interaction.channel.history(limit=50).flatten()
    
        # Find the last image uploaded by the user
        image_url = None
        for message in messages:
            if message.author == interaction.user and message.attachments:
                image_url = message.attachments[0].url
                break
    
        if image_url:
            # Download the image and save it locally
            file_name = "ai_resources/new_images/uploaded_image.png"
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        return await interaction.response.send_message("Could not download file...", ephemeral=True)
                    data = await resp.read()
                    with open(file_name, 'wb') as f:
                        f.write(data)
    
            # Process the image using the process_image function
            processed_image_path = process_image(file_name)
    
            # Run the vary_image function on the processed image
            await self.vary_image(interaction, processed_image_path, resolution)
        else:
            await interaction.response.send_message("Please upload an image.", ephemeral=True)


# Function to set up the Paint cog
def setup(bot):
    bot.add_cog(Paint(bot))

