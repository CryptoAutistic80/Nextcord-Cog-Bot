import nextcord
from nextcord.ext import commands
import openai
import json
import os
import sqlite3
from datetime import datetime
from collections import deque

class EndConversationButton(nextcord.ui.Button):
    def __init__(self, cog, user_id):
        super().__init__(label="End", style=nextcord.ButtonStyle.blurple)
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: nextcord.Interaction):
        # Get the conversation history
        history = self.cog.conversations[self.user_id]

        # Store the conversation history in the database
        for message in history:
            timestamp = datetime.now().isoformat()
            user_id = self.user_id
            role = message['role']
            content = message['content']
            self.cog.c.execute('''
                INSERT INTO history (timestamp, user_id, role, content)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, user_id, role, content))
        self.cog.conn.commit()

        # End the conversation
        del self.cog.conversations[self.user_id]
        # Delete the thread
        await interaction.channel.delete()

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Set the OpenAI API key from the environment variable
        openai.api_key = os.getenv('Key_OpenAI')
        # Initialize a dictionary to store conversation histories for each user
        self.conversations = {}

        # Load the initial message from the JSON file
        with open('json/helius_prompt.json') as f:
            self.initial_message = json.load(f)['messages'][0]

        # Connect to the database
        self.connect_to_db()

    def connect_to_db(self):
        self.conn = sqlite3.connect('conversation_history.db')
        self.c = self.conn.cursor()
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS history (
                timestamp TEXT,
                user_id INTEGER,
                role TEXT,
                content TEXT
            )
        ''')
        self.conn.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        print("ChatCog is online!")

    @nextcord.slash_command(description="Start a chat with HELIUS")
    async def chat(self, interaction: nextcord.Interaction):
        # Defer the interaction, indicating that the bot is thinking
        await interaction.response.defer(ephemeral=True)

        # Get the user's ID
        user_id = interaction.user.id

        # Retrieve the 20 most recent messages for this user from the database
        self.c.execute('''
            SELECT role, content
            FROM history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 20
        ''', (user_id,))
        recent_messages = [{'role': role, 'content': content} for role, content in self.c.fetchall()]

        # If this user has no conversation history, initialize it with the initial message from the JSON file
        if user_id not in self.conversations:
            self.conversations[user_id] = deque(maxlen=20)
            self.conversations[user_id].append(self.initial_message)

        # Append the recent messages to the initial message
        self.conversations[user_id].extend(recent_messages)

        # Start a new private thread
        thread = await interaction.channel.create_thread(name=f"Chat with {interaction.user.name}", type=nextcord.ChannelType.private_thread)

        # Create a view with the end conversation button
        view = nextcord.ui.View()
        view.add_item(EndConversationButton(self, user_id))

        #Send a welcome message to the thread
        await thread.send(f"Welcome to the chat {interaction.user.mention}! You can start by typing a message.", view=view)

        # Send an ephemeral message to the user to fulfill the deferred response
        await interaction.followup.send("A private thread has been created for your chat.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from bots
        if message.author.bot:
            return
          
        # Ignore messages that are not in a thread
        if not isinstance(message.channel, nextcord.Thread):
            return
    
        # Ignore messages that are not in a private thread
        if message.channel.type != nextcord.ChannelType.private_thread:
            return
    
        # Get the user's ID
        user_id = message.author.id
    
        # Ignore messages from users who have no conversation history
        if user_id not in self.conversations:
            return
    
        # Add the user's message to their conversation history
        self.conversations[user_id].append({"role": "user", "content": message.content})
    
        # Indicate that the bot is typing
        async with message.channel.typing():
            # Create a chat completion with the user's conversation history
            # Include the initial message at the beginning of the conversation history
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[self.initial_message] + list(self.conversations[user_id])
            )
    
            # Extract the assistant's reply from the response
            assistant_reply = response['choices'][0]['message']['content']
    
            # Add the assistant's reply to the user's conversation history
            self.conversations[user_id].append({"role": "assistant", "content": assistant_reply})
    
            # Create a view with the end conversation button
            view = nextcord.ui.View()
            view.add_item(EndConversationButton(self, user_id))
    
            # Send the assistant's reply to the thread with the view
            await message.channel.send(assistant_reply, view=view)

def setup(bot):
    bot.add_cog(ChatCog(bot))
