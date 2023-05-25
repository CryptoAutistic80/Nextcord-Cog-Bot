import nextcord
from nextcord.ext import commands
import aiohttp

class Administrator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Administrator is online!")

    @nextcord.slash_command(description="Uploads the most recent PDF files sent by the user")
    async def pdf_upload(self, interaction: nextcord.Interaction, num_pdfs: int = 1):
        # Check if the user has admin permissions
        if interaction.user.guild_permissions.administrator:
            # Defer the response to indicate that the bot is thinking
            await interaction.response.defer()

            # Find the most recent PDF attachments sent by the user
            messages = await interaction.channel.history(limit=50).flatten()
            pdf_files = []
            for message in messages:
                if message.author == interaction.user:
                    for attachment in message.attachments:
                        if attachment.filename.endswith('.pdf'):
                            pdf_files.append(attachment)
                            if len(pdf_files) >= num_pdfs:
                                break
                if len(pdf_files) >= num_pdfs:
                    break

            # If any PDF files were found, download and save them
            if pdf_files:
                for pdf_file in pdf_files:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(pdf_file.url) as resp:
                            if resp.status == 200:
                                with open(f'ai_resources/pdf_documents/{pdf_file.filename}', 'wb') as f:
                                    f.write(await resp.read())
                # Send an ephemeral message confirming the upload
                await interaction.followup.send(f"{len(pdf_files)} PDF file(s) have been uploaded successfully.", ephemeral=True)
            else:
                await interaction.followup.send("No recent PDF files found.", ephemeral=True)
        else:
            # Send an ephemeral message stating that the user lacks the permissions to use this command
            await interaction.response.send_message("You lack the permissions to use this command.", ephemeral=True)

def setup(bot):
    bot.add_cog(Administrator(bot))


