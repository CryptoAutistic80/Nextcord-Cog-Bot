import nextcord  # Importing the nextcord library, a Python wrapper for the Discord API

# Defining a class named ImageButton that extends nextcord.ui.Button
class ImageButton(nextcord.ui.Button):
    def __init__(self, label, image_path):
        super().__init__(label=label, style=nextcord.ButtonStyle.primary)
        self.image_path = image_path

    async def callback(self, interaction: nextcord.Interaction):
        with open(self.image_path, 'rb') as f:
            picture = nextcord.File(f)
            await interaction.response.send_message(file=picture, ephemeral=True)

# Defining a class named RegenerateButton that extends nextcord.ui.Button
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

# Defining a class named RegenerateVaryButton that extends nextcord.ui.Button
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

# Defining a class named VaryButton that extends nextcord.ui.Button
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
