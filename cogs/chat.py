import nextcord
from nextcord.ext import commands
import openai
import asyncio
import json
import os
import sqlite3
from collections import deque
from modules.buttons import EndConversationButton, EndWithoutSaveButton

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        openai.api_key = os.getenv('Key_OpenAI')
        self.conversations = {}
        self.last_bot_messages = {}
        self.models = {}
        self.threads = {}

        with open('json/helius_prompt.json') as f:
            self.initial_message = json.load(f)['messages'][0]

        self.connect_to_db()

    def connect_to_db(self):
        self.conn = sqlite3.connect('ai_resources/conversation_history.db')
        self.c = self.conn.cursor()
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS history (
                timestamp TEXT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                keywords TEXT
            )
        ''')
        self.conn.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        print("ChatCog is online!")

    @nextcord.slash_command(description="Start a chat with HELIUS")
    async def chat(self, interaction: nextcord.Interaction, model: str = nextcord.SlashOption(
        choices={"GPT-4": "gpt-4", "GPT-3.5-TURBO": "gpt-3.5-turbo"},
        description="Choose the model for the chat"
    )):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
    
        if user_id in self.threads:
            try:
                thread = await self.bot.fetch_channel(self.threads[user_id].id)
            except nextcord.NotFound:
                del self.threads[user_id]
            else:
                await interaction.followup.send("You already have an open chat thread. Please use that one.", ephemeral=True)
                return
    
        self.c.execute('''
            SELECT role, content
            FROM history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (user_id,))
        recent_messages = [{'role': role, 'content': content} for role, content in self.c.fetchall()]
    
        if user_id not in self.conversations:
            self.conversations[user_id] = deque(maxlen=10)
            self.conversations[user_id].append(self.initial_message)
    
        self.conversations[user_id].extend(recent_messages)
        self.models[user_id] = model
    
        thread = await interaction.channel.create_thread(name=f"Chat with {interaction.user.name}", type=nextcord.ChannelType.private_thread)
        self.threads[user_id] = thread
    
        # Add view to initial message
        initial_view = nextcord.ui.View()
        initial_view.add_item(EndWithoutSaveButton(self, user_id))
        initial_message = await thread.send(f"Welcome to the chat {interaction.user.mention}! You can start by typing a message.", view=initial_view)

        # Store the initial message
        self.last_bot_messages[user_id] = initial_message
        
        await interaction.followup.send("A private thread has been created for your chat.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not isinstance(message.channel, nextcord.Thread):
            return
        if message.channel.type != nextcord.ChannelType.private_thread:
            return
    
        user_id = message.author.id
        if user_id not in self.conversations:
            return
    
        # Check if this is the first user message in the thread
        if len(self.conversations[user_id]) == 1:
            # Fetch the initial welcome message
            initial_message = self.last_bot_messages[user_id]
            await initial_message.edit(view=None) # remove the buttons from the initial message
    
        self.conversations[user_id].append({"role": "user", "content": message.content})
        thinking_message = await message.channel.send("HELIUS is thinking...please don't message again even if it appears I'm not typing. Remember I'm not a supercomputer....yet!")

        async with message.channel.typing():
            for attempt in range(30):
                try:
                    response = openai.ChatCompletion.create(
                        model=self.models[user_id],
                        messages=[self.initial_message] + list(self.conversations[user_id])
                    )
                    break
                except openai.OpenAIError:
                    if attempt == 29:
                        await message.channel.send("Sorry the API is a bit jammed up, hold tight and try again soon. Thanks human.")
                        return
                    else:
                        await asyncio.sleep(1)

            assistant_reply = response['choices'][0]['message']['content']
            self.conversations[user_id].append({"role": "assistant", "content": assistant_reply})

            if user_id in self.last_bot_messages:
                try:
                    last_bot_message = self.last_bot_messages[user_id]
                    await last_bot_message.edit(view=None)
                except nextcord.errors.NotFound:
                    pass  

            view = nextcord.ui.View()
            view.add_item(EndConversationButton(self, user_id))
            view.add_item(EndWithoutSaveButton(self, user_id))
            await thinking_message.delete()
            new_bot_message = await message.channel.send(assistant_reply, view=view)
            self.last_bot_messages[user_id] = new_bot_message

def setup(bot):
    bot.add_cog(ChatCog(bot))

