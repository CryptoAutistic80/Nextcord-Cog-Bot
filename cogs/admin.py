import nextcord                        # Module for creating Discord bots
from nextcord.ext import commands      # Specific class from the nextcord module
import aiohttp                         # Module for making HTTP requests asynchronously
import json                            # Module for working with JSON data
import uuid                            # Module for generating UUIDs
from datetime import datetime          # Module for working with dates and times
from modules.keywords import get_keywords  # Import a custom module 'get_keywords' from the 'modules' package

# Define a class 'Administrator' that extends 'commands.Cog'
class Administrator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("ADMIN HERE")  # Print a message when the bot is ready

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

        # Defer the interaction response to indicate that the bot is working on the request
        await interaction.response.defer()

        user_id = user.id

        # Save the conversation to the database
        chat_cog = self.bot.get_cog('ChatCog')
        if user_id in chat_cog.conversations:
            history = chat_cog.conversations[user_id]
            keywords_metadata = await get_keywords([msg for msg in list(history) if msg['role'] != 'system'])

            # Retrieve the UUID for the chat session
            chat_uuid = chat_cog.chat_uuids.get(user_id)

            for message in history:
                if message['role'] != 'system':
                    timestamp = datetime.now().isoformat()
                    role = message['role']
                    content = message['content']
                    keywords = json.dumps(keywords_metadata)
                    await chat_cog.c.execute(
                        '''
                        INSERT INTO history (timestamp, user_id, role, content, keywords, uuid)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''', (timestamp, user_id, role, content, keywords, chat_uuid))
            await chat_cog.conn.commit()

            del chat_cog.conversations[user_id]

        # Check if the key exists before deleting it
        if user_id in chat_cog.models:
            del chat_cog.models[user_id]
        if user_id in chat_cog.last_bot_messages:
            del chat_cog.last_bot_messages[user_id]

        # Delete the thread
        if user_id in chat_cog.threads:
            thread = chat_cog.threads[user_id]
            await thread.delete()
            if user_id in chat_cog.threads:  # Check again just in case the key was deleted in on_thread_delete
                del chat_cog.threads[user_id]
            if user_id in chat_cog.chat_uuids:
                del chat_cog.chat_uuids[user_id]

        # Send a follow-up message to the channel
        await interaction.followup.send("The users chat has been ended and saved successfully.")

# Function to set up the 'Administrator' cog
def setup(bot):
    bot.add_cog(Administrator(bot))
