import nextcord
from modules.keywords import get_keywords
from datetime import datetime
import json
import asyncio

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
        await interaction.followup.send("🔄 Trying again human...", ephemeral=True)
        await self.cog.generate_image(interaction, self.prompt, self.size)

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
        await self.cog.vary_image(interaction, self.image_path, self.size)

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
        await self.cog.vary_image(interaction, self.image_path, self.size)

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

                    for message in history:
                        if message['role'] != 'system':
                            timestamp = datetime.now().isoformat()
                            user_id = self.user_id
                            role = message['role']
                            content = message['content']
                            keywords = json.dumps(keywords_metadata)
                            await self.cog.c.execute(
                                '''
                                INSERT INTO history (timestamp, user_id, role, content, keywords)
                                VALUES (?, ?, ?, ?, ?)
                                ''', (timestamp, user_id, role, content, keywords))
                    await self.cog.conn.commit()

                    del self.cog.conversations[self.user_id]
                    if self.user_id in self.cog.threads:
                        del self.cog.threads[self.user_id]
                    if self.user_id in self.cog.models:
                        del self.cog.models[self.user_id]
                    if self.user_id in self.cog.last_bot_messages:
                        del self.cog.last_bot_messages[self.user_id]

            await interaction.channel.delete()
        except Exception as e:
            print(f"An error occurred: {e}")

class EndWithoutSaveButton(nextcord.ui.Button):
    def __init__(self, cog, user_id):
        super().__init__(label="End without save", style=nextcord.ButtonStyle.red)
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: nextcord.Interaction):
        try:
            async with self.cog.lock:
                if self.user_id in self.cog.conversations:
                    del self.cog.conversations[self.user_id]
                    if self.user_id in self.cog.threads:
                        del self.cog.threads[self.user_id]
                    if self.user_id in self.cog.models:
                        del self.cog.models[self.user_id]
                    if self.user_id in self.cog.last_bot_messages:
                        del self.cog.last_bot_messages[self.user_id]
            await interaction.channel.delete()
        except Exception as e:
            print(f"An error occurred: {e}")



