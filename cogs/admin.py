import nextcord
from nextcord.ext import commands
import aiohttp
import asyncio
import json
from modules.keywords import get_keywords
from datetime import datetime
from cogs.chat import ChatCog

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

    @nextcord.slash_command(description="Ends a chat with HELIUS (Admin only)")
    async def end_chat_save(self, interaction: nextcord.Interaction, user: nextcord.User = nextcord.SlashOption(description="The user whose chat should be ended")):
        # Check if the command is being used in a private thread
        if isinstance(interaction.channel, nextcord.Thread) and interaction.channel.type == nextcord.ChannelType.private_thread:
            await interaction.response.send_message("This command can't be used in a private thread.", ephemeral=True)
            return
    
        # Check for admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only an admin can use this command.", ephemeral=True)
            return
    
        user_id = user.id
    
        # Access the instance of ChatCog from the bot instance and replicate the functionality of EndConversationButton here
        chat_cog = self.bot.get_cog('ChatCog')
        if user_id in chat_cog.conversations:
            history = chat_cog.conversations[user_id]
            keywords_metadata = get_keywords([msg for msg in list(history) if msg['role'] != 'system'])
    
            for message in history:
                if message['role'] != 'system':
                    timestamp = datetime.now().isoformat()
                    role = message['role']
                    content = message['content']
                    keywords = json.dumps(keywords_metadata)
                    chat_cog.c.execute('''
                        INSERT INTO history (timestamp, user_id, role, content, keywords)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (timestamp, user_id, role, content, keywords))
            chat_cog.conn.commit()
    
            del chat_cog.conversations[user_id]
    
        # Delete the thread
        if user_id in chat_cog.threads:
            thread = chat_cog.threads[user_id]
            await thread.delete()
            del chat_cog.threads[user_id]
    
        # Send an ephemeral message to the channel
        await interaction.response.send_message(f"The chat with user {user.name} has been ended and saved successfully.", ephemeral=True)


def setup(bot):
    bot.add_cog(Administrator(bot))


