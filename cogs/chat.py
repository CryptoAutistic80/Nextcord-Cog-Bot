import asyncio                    # Module for asynchronous programming
import uuid                       # UUID generation
import json                       # Module for working with JSON data
import logging                    # Module for logging events
import openai                     # Module for interacting with the OpenAI API
import aiosqlite                  # Module for working with SQLite databases asynchronously
import nextcord                   # Module for creating Discord bots
from nextcord.ext import commands # Specific class from the nextcord module
from collections import deque     # Container datatype that stores a fixed-size collection of elements
from modules.buttons import EndConversationButton, EndWithoutSaveButton  # Import custom button modules

logger = logging.getLogger('discord')

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversations = {}  # Dictionary to store conversations with users
        self.chat_uuids = {}  # Dictionary for storing UUIDs of chat sessions.
        self.last_bot_messages = {}  # Dictionary to store the last bot message sent to users
        self.models = {}  # Dictionary to store models for each user
        self.threads = {}  # Dictionary to store threads for each user
        self.lock = asyncio.Lock()  # Lock for synchronizing access to shared resources

        self._db_task = asyncio.ensure_future(self.connect_to_db())  # Task for connecting to the database asynchronously

    async def connect_to_db(self):
        logger.info("Starting to connect to DB")
        self.conn = await aiosqlite.connect('ai_resources/conversation_history.db')  # Connect to the SQLite database
        self.c = await self.conn.cursor()
        await self.c.execute('''
            CREATE TABLE IF NOT EXISTS history (
                timestamp TEXT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                keywords TEXT,
                uuid TEXT
            )
            ''')
        await self.conn.commit()
        logger.info("Finished connecting to DB")

    async def close(self):
        for thread_id, thread in self.threads.items():
            try:
                fetched_thread = await self.bot.fetch_channel(thread_id)  # Fetch the thread from Discord
                await fetched_thread.delete()  # Delete the thread
                logging.info(f"Thread for user {thread_id} closed in close function")
            except (nextcord.NotFound, nextcord.HTTPException):
                continue

        if hasattr(self, 'c'):
            await self.c.close()  # Close the database cursor
        if hasattr(self, 'conn'):
            await self.conn.close()  # Close the database connection
        await self._db_task
        logger.info("Successfully closed all threads and database connections")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Chat loaded")

    @nextcord.slash_command(description="Start a chat with HELIUS")
    async def chat(self, interaction: nextcord.Interaction, model: str = nextcord.SlashOption(
        choices={"GPT-3.5-TURBO": "gpt-3.5-turbo", "GPT-4": "gpt-4"},
        description="Choose the model for the chat"
    ), personality: str = nextcord.SlashOption(
        choices={
            "Default": "helius_prompt",
            "Nikola Tesla": "tesla_prompt",
            "Charles Darwin": "darwin_prompt",
            "Napoleon Bonaparte": "napoleon_prompt",
            "Teddy Roosevelt": "teddy_prompt",
            "Ghandi": "ghandi_prompt"
        },
        description="Choose the personality for the chat (only applicable for GPT-4)",
        default="helius_prompt"
    )):
        async with self.lock:
            try:
                await interaction.response.defer(ephemeral=True)  # Defer the initial response to the interaction
            except nextcord.NotFound:
                return

            user_id = interaction.user.id

            # Create a new UUID for this user's chat session
            self.chat_uuids[user_id] = str(uuid.uuid4())

            if user_id in self.threads:
                try:
                    thread = await self.bot.fetch_channel(self.threads[user_id].id)  # Fetch the thread from Discord
                except nextcord.NotFound:
                    del self.threads[user_id]
                else:
                    await interaction.followup.send("You already have an open chat thread. Please use that one.", ephemeral=True)
                    return

            if self.conn is None or self.c is None:
                await self.connect_to_db()  # Connect to the database if not already connected

            logger.info("Starting DB operation")
            await self.c.execute('''
                SELECT role, content
                FROM history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 18
            ''', (user_id,))
            recent_messages = [{'role': role, 'content': content} for role, content in await self.c.fetchall()]
            logger.info("Finished DB operation")

            if personality is None or model == "gpt-3.5-turbo":
                personality = "helius_prompt"
            with open(f'json/{personality}.json') as f:
                self.initial_message = json.load(f)['messages'][0]  # Load the initial message from the JSON file

            if user_id not in self.conversations:
                self.conversations[user_id] = deque(maxlen=18)  # Create a deque to store conversation messages
                self.conversations[user_id].append(self.initial_message)  # Append the initial message

            self.conversations[user_id].extend(reversed(recent_messages))
            self.models[user_id] = model  # Store the model for the user

            thread = await interaction.channel.create_thread(name=f"Chat with {interaction.user.name}", type=nextcord.ChannelType.private_thread)  # Create a private thread
            self.threads[user_id] = thread
            logging.info(f"Thread created for user {user_id} in chat function")

            initial_view = nextcord.ui.View()  # Create a view for buttons
            initial_view.add_item(EndWithoutSaveButton(self, user_id))  # Add an "End without Save" button
            initial_message = await thread.send(f"Welcome to the chat {interaction.user.mention}! You can start by typing a message.", view=initial_view)  # Send an initial message to the thread

            self.last_bot_messages[user_id] = initial_message  # Store the initial message as the last bot message

            await interaction.followup.send("A private thread has been created for your chat.", ephemeral=True)
            logger.info(f"User {user_id} started a chat session using model: {model}")

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

        # Append the user message to the conversation
        self.conversations[user_id].append({
            'role': 'user',
            'content': message.content,
        })

        if len(self.conversations[user_id]) == 1:
            initial_message = self.last_bot_messages[user_id]
            await initial_message.edit(view=None)

        thinking_message = await message.channel.send("HELIUS is thinking...please don't message again even if it appears I'm not typing. Remember I'm not a supercomputer....yet!")

        async with message.channel.typing():
            for attempt in range(30):
                try:
                    logger.info("Starting OpenAI call")
                    response = await asyncio.to_thread(
                        openai.ChatCompletion.create,
                        model=self.models[user_id],
                        messages=[self.initial_message] + list(self.conversations[user_id])
                    )  # Call the OpenAI API to get a response
                    logger.info("Finished OpenAI call")
                    break
                except openai.OpenAIError as e:
                    logger.error(f"Error while calling OpenAI API: {str(e)}")
                    if attempt == 29:
                        await self.send_message_safe("Sorry the API is a bit jammed up, hold tight and try again soon. Thanks human.")
                        return
                    elif 'rate limit' in str(e):
                        await asyncio.sleep(60)  # Wait for 60 seconds before retrying
                    else:
                        await asyncio.sleep(1)  # Wait for 1 second before retrying

        assistant_reply = response['choices'][0]['message']['content']  # Extract the assistant's reply from the response

        # Append the assistant's reply to the conversation
        self.conversations[user_id].append({
            'role': 'assistant',
            'content': assistant_reply,
        })

        if user_id in self.last_bot_messages:
            last_bot_message = self.last_bot_messages[user_id]
            await last_bot_message.edit(view=None)  # Remove the buttons from the last bot message

        new_view = nextcord.ui.View()  # Create a new view for buttons
        new_view.add_item(EndConversationButton(self, user_id))  # Add an "End Conversation" button
        new_view.add_item(EndWithoutSaveButton(self, user_id))  # Add an "End without Save" button
        new_bot_message = await self.send_message_safe(message.channel.send(assistant_reply, view=new_view))  # Send the assistant's reply with buttons

        self.last_bot_messages[user_id] = new_bot_message  # Update the last bot message

        await thinking_message.delete()  # Delete the thinking message

    async def send_message_safe(self, coro):
        try:
            return await coro
        except nextcord.NotFound:
            pass
        except Exception as e:
            logger.error(f"Error while sending message: {str(e)}")

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        if thread.id in self.threads:
            user_id = self.threads[thread.id]
            if user_id in self.conversations:
                del self.conversations[user_id]
            if user_id in self.models:  # Check if the key exists before deleting
                del self.models[user_id]
            if user_id in self.last_bot_messages:  # Check if the key exists before deleting
                del self.last_bot_messages[user_id]
            if user_id in self.chat_uuids:  # Check if the key exists before deleting
                del self.chat_uuids[user_id]
            del self.threads[thread.id]

def setup(bot):
    bot.add_cog(ChatCog(bot))  # Add the ChatCog as a cog to the bot
