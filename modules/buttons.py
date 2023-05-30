import nextcord  # Library for building discord bots
from modules.keywords import get_keywords  # Module for keyword extraction
from datetime import datetime  # For getting current time
import json  # JSON parsing
import uuid  # UUID generation
import asyncio  # Asynchronous programming in Python

# The ImageButton class defines a button in the Discord UI that sends an image when clicked.
class ImageButton(nextcord.ui.Button):
    def __init__(self, label, image_path):
        super().__init__(label=label, style=nextcord.ButtonStyle.primary)  # Button initialization
        self.image_path = image_path  # Path to the image that this button sends

    async def callback(self, interaction: nextcord.Interaction):
        # Callback function when this button is clicked.
        with open(self.image_path, 'rb') as f:  # Open the image file in binary mode
            picture = nextcord.File(f)  # Convert the image file to a Discord file
            await interaction.response.send_message(file=picture, ephemeral=True)  # Send the image in response

# The RegenerateButton class defines a button in the Discord UI that regenerates an image when clicked.
class RegenerateButton(nextcord.ui.Button):
    def __init__(self, size, prompt, cog):
        super().__init__(style=nextcord.ButtonStyle.primary, label="🔄")
        self.size = size
        self.prompt = prompt
        self.cog = cog

    async def callback(self, interaction: nextcord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("🔄 Trying again human...", ephemeral=True)
        await self.cog.generate_image(interaction, self.prompt, self.size)  # Call generate_image method from cog

# The RegenerateVaryButton class defines a button in the Discord UI that regenerates a variant image when clicked.
class RegenerateVaryButton(nextcord.ui.Button):
    def __init__(self, size, image_path, cog):
        super().__init__(style=nextcord.ButtonStyle.primary, label="🔄")
        self.size = size
        self.image_path = image_path
        self.cog = cog

    async def callback(self, interaction: nextcord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("🚀 Activating variation drive...", ephemeral=True)
        await self.cog.vary_image(interaction, self.image_path, self.size)  # Call vary_image method from cog

# The VaryButton class defines a button in the Discord UI that creates variations of an image when clicked.
class VaryButton(nextcord.ui.Button):
    def __init__(self, label, image_path, size, cog):
        super().__init__(label=label, style=nextcord.ButtonStyle.secondary)
        self.image_path = image_path
        self.size = size
        self.cog = cog

    async def callback(self, interaction: nextcord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("💫 Spinning some variety...", ephemeral=True)
        await self.cog.vary_image(interaction, self.image_path, self.size)  # Call vary_image method from cog

# The EndConversationButton class defines a button in the Discord UI that ends a conversation and saves it.
class EndConversationButton(nextcord.ui.Button):
    def __init__(self, cog, user_id):
        super().__init__(label="End", style=nextcord.ButtonStyle.blurple)
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: nextcord.Interaction):
        try:
            async with self.cog.lock:
                if self.user_id in self.cog.conversations:
                    history = self.cog.conversations[self.user_id]
                    keywords_metadata = await get_keywords([msg for msg in list(history) if msg['role'] != 'system'])

                    # Retrieve the UUID for the chat session
                    chat_uuid = self.cog.chat_uuids.get(self.user_id)

                    # Code block for saving the chat history to a database
                    for message in history:
                        if message['role'] != 'system':
                            timestamp = datetime.now().isoformat()
                            user_id = self.user_id
                            role = message['role']
                            content = message['content']
                            keywords = json.dumps(keywords_metadata)
                            await self.cog.c.execute(
                                '''
                                INSERT INTO history (timestamp, user_id, role, content, keywords, uuid)
                                VALUES (?, ?, ?, ?, ?, ?)
                                ''', (timestamp, user_id, role, content, keywords, chat_uuid))
                    await self.cog.conn.commit()

                    # Delete this conversation from memory
                    del self.cog.conversations[self.user_id]
                    if self.user_id in self.cog.threads:
                        del self.cog.threads[self.user_id]
                    if self.user_id in self.cog.models:
                        del self.cog.models[self.user_id]
                    if self.user_id in self.cog.last_bot_messages:
                        del self.cog.last_bot_messages[self.user_id]
                    if self.user_id in self.cog.chat_uuids:
                        del self.cog.chat_uuids[self.user_id]
                    

            await interaction.channel.delete()  # Delete the conversation channel
        except Exception as e:
            print(f"An error occurred: {e}")

# The EndWithoutSaveButton class defines a button in the Discord UI that ends a conversation without saving it.
class EndWithoutSaveButton(nextcord.ui.Button):
    def __init__(self, cog, user_id):
        super().__init__(label="End without save", style=nextcord.ButtonStyle.red)
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: nextcord.Interaction):
        try:
            async with self.cog.lock:
                if self.user_id in self.cog.conversations:
                    # Delete this conversation from memory
                    del self.cog.conversations[self.user_id]
                    if self.user_id in self.cog.threads:
                        del self.cog.threads[self.user_id]
                    if self.user_id in self.cog.models:
                        del self.cog.models[self.user_id]
                    if self.user_id in self.cog.last_bot_messages:
                        del self.cog.last_bot_messages[self.user_id]
                    if self.user_id in self.cog.chat_uuids:
                        del self.cog.chat_uuids[self.user_id]

            await interaction.channel.delete()  # Delete the conversation channel
        except Exception as e:
            print(f"An error occurred: {e}")
