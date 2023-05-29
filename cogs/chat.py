import asyncio
import json
import logging
import openai
import aiosqlite
import nextcord
from nextcord.ext import commands
from collections import deque
from modules.buttons import EndConversationButton, EndWithoutSaveButton

logger = logging.getLogger('discord')

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversations = {}
        self.last_bot_messages = {}
        self.models = {}
        self.threads = {}
        self.lock = asyncio.Lock()

        self._db_task = asyncio.ensure_future(self.connect_to_db())

    async def connect_to_db(self):
        logger.info("Starting to connect to DB")
        self.conn = await aiosqlite.connect('ai_resources/conversation_history.db')
        self.c = await self.conn.cursor()
        await self.c.execute('''
            CREATE TABLE IF NOT EXISTS history (
                timestamp TEXT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                keywords TEXT
            )
        ''')
        await self.conn.commit()
        logger.info("Finished connecting to DB")

    async def close(self):
        for thread_id, thread in self.threads.items():
            try:
                fetched_thread = await self.bot.fetch_channel(thread_id)
                await fetched_thread.delete()
                logging.info(f"Thread for user {thread_id} closed in close function")
            except (nextcord.NotFound, nextcord.HTTPException):
                continue

        if hasattr(self, 'c'):
            await self.c.close()
        if hasattr(self, 'conn'):
            await self.conn.close()
        await self._db_task
        logger.info("Successfully closed all threads and database connections")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Chat loaded")

    @nextcord.slash_command(description="Start a chat with HELIUS")
    async def chat(self, interaction: nextcord.Interaction, model: str = nextcord.SlashOption(
        choices={"GPT-4": "gpt-4", "GPT-3.5-TURBO": "gpt-3.5-turbo"},
        description="Choose the model for the chat"
    ), personality: str = nextcord.SlashOption(
        choices={"Default": "helius_prompt", "Nikola Tesla": "tesla_prompt", "Charles Darwin": "darwin_prompt",
                 "Napoleon Bonaparte": "napoleon_prompt", "Teddy Roosevelt": "teddy_prompt", "Ghandi": "ghandi_prompt"},
        description="Choose the personality for the chat",
        required=False)):
        async with self.lock:
            try:
                await interaction.response.defer(ephemeral=True)
            except nextcord.NotFound:
                return

            user_id = interaction.user.id

            if user_id in self.threads:
                try:
                    thread = await self.bot.fetch_channel(self.threads[user_id].id)
                except nextcord.NotFound:
                    del self.threads[user_id]
                else:
                    await interaction.followup.send("You already have an open chat thread. Please use that one.", ephemeral=True)
                    return

            if self.conn is None or self.c is None:
                await self.connect_to_db()

            logger.info("Starting DB operation")
            await self.c.execute('''
                SELECT role, content
                FROM history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (user_id,))
            recent_messages = [{'role': role, 'content': content} for role, content in await self.c.fetchall()]
            logger.info("Finished DB operation")

            if personality is None or model == "gpt-3.5-turbo":
                personality = "helius_prompt"
            with open(f'json/{personality}.json') as f:
                self.initial_message = json.load(f)['messages'][0]

            if user_id not in self.conversations:
                self.conversations[user_id] = deque(maxlen=10)
                self.conversations[user_id].append(self.initial_message)

            self.conversations[user_id].extend(recent_messages)
            self.models[user_id] = model

            thread = await interaction.channel.create_thread(name=f"Chat with {interaction.user.name}", type=nextcord.ChannelType.private_thread)
            self.threads[user_id] = thread
            logging.info(f"Thread created for user {user_id} in chat function")

            initial_view = nextcord.ui.View()
            initial_view.add_item(EndWithoutSaveButton(self, user_id))
            initial_message = await thread.send(f"Welcome to the chat {interaction.user.mention}! You can start by typing a message.", view=initial_view)

            self.last_bot_messages[user_id] = initial_message

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

        if len(self.conversations[user_id]) == 1:
            initial_message = self.last_bot_messages[user_id]
            await initial_message.edit(view=None)

        self.conversations[user_id].append({"role": "user", "content": message.content})
        thinking_message = await message.channel.send("HELIUS is thinking...please don't message again even if it appears I'm not typing. Remember I'm not a supercomputer....yet!")

        async with message.channel.typing():
            for attempt in range(30):
                try:
                    logger.info("Starting OpenAI call")
                    response = await asyncio.to_thread(
                        openai.ChatCompletion.create,
                        model=self.models[user_id],
                        messages=[self.initial_message] + list(self.conversations[user_id])
                    )
                    logger.info("Finished OpenAI call")
                    break
                except openai.OpenAIError as e:
                    logger.error(f"Error while calling OpenAI API: {str(e)}")
                    if attempt == 29:
                        await self.send_message_safe(message.channel, "Sorry the API is a bit jammed up, hold tight and try again soon. Thanks human.")
                        return
                    elif 'rate limit' in str(e):
                        await asyncio.sleep(60)
                    else:
                        await asyncio.sleep(1)

        assistant_reply = response['choices'][0]['message']['content']
        self.conversations[user_id].append({"role": "assistant", "content": assistant_reply})

        if user_id in self.last_bot_messages:
            last_bot_message = self.last_bot_messages[user_id]
            await self.send_message_safe(last_bot_message.edit(view=None))

        new_view = nextcord.ui.View()
        new_view.add_item(EndConversationButton(self, user_id))
        new_view.add_item(EndWithoutSaveButton(self, user_id))
        new_bot_message = await self.send_message_safe(message.channel.send(assistant_reply, view=new_view))

        self.last_bot_messages[user_id] = new_bot_message

        await self.send_message_safe(thinking_message.delete())

    async def send_message_safe(self, action):
        try:
            return await action
        except nextcord.errors.NotFound:
            pass

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        user_id = next((k for k, v in self.threads.items() if v.id == thread.id), None)
        if user_id:
            del self.threads[user_id]
            del self.models[user_id]
            if user_id in self.conversations:
                del self.conversations[user_id]
            if user_id in self.last_bot_messages:
                del self.last_bot_messages[user_id]
            logger.info(f"Thread deleted for user {user_id}, removed user data from memory")

def setup(bot):
    bot.add_cog(ChatCog(bot))

