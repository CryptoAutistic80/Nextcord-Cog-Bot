import asyncio
import uuid
import json
import logging
import openai
import aiosqlite
import nextcord
from nextcord.ext import commands
from collections import deque
from modules.buttons import EndConversationButton, EndWithoutSaveButton

import os
import pinecone

OPENAI_KEY = os.getenv('Key_OpenAI')
PINECONE_KEY = os.getenv('PINECONE_KEY')
output_path = "ai_resources/embeddings"

logger = logging.getLogger('discord')

def gpt_embed(text):
    content = text.encode(encoding='ASCII', errors='ignore').decode()  # Fix any UNICODE errors
    openai.api_key = OPENAI_KEY
    response = openai.Embedding.create(
        input=content,
        engine='text-embedding-ada-002'
    )
    vector = response['data'][0]['embedding']  # This is a normal list
    return vector

# Initialize pinecone
pinecone.init(api_key=PINECONE_KEY, environment='us-east1-gcp')
pinecone_indexer = pinecone.Index("core-69")

async def query_pinecone(query_vector_np, top_k=5, namespace="library"):
    query_results = pinecone_indexer.query(
        vector=query_vector_np,
        top_k=top_k,
        namespace=namespace,
    )
    metadata_list = []
    for match in query_results['matches']:
        uuid_val = match['id']
        with open(os.path.join(output_path, f'{uuid_val}.json'), 'r') as f:
            metadata = json.load(f)
        metadata_list.append(metadata)
    return metadata_list

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_semaphore = asyncio.Semaphore(10)
        self.conversations = {}
        self.chat_uuids = {}
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
                keywords TEXT,
                uuid TEXT
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
                await interaction.response.defer(ephemeral=True)
            except nextcord.NotFound:
                return

            user_id = interaction.user.id
            self.chat_uuids[user_id] = str(uuid.uuid4())

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
                LIMIT 18
            ''', (user_id,))
            recent_messages = [{'role': role, 'content': content} for role, content in await self.c.fetchall()]
            logger.info("Finished DB operation")

            if personality is None or model == "gpt-3.5-turbo":
                personality = "helius_prompt"
            with open(f'json/{personality}.json') as f:
                self.initial_message = json.load(f)['messages'][0]

            if user_id not in self.conversations:
                self.conversations[user_id] = deque(maxlen=18)
                self.conversations[user_id].append(self.initial_message)

            self.conversations[user_id].extend(reversed(recent_messages))
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

        self.conversations[user_id].append({
            'role': 'user',
            'content': message.content,
        })

        if len(self.conversations[user_id]) == 1:
            initial_message = self.last_bot_messages[user_id]
            await initial_message.edit(view=None)

        thinking_message = await message.channel.send("HELIUS is thinking...please don't message again even if it appears I'm not typing. Remember I'm not a supercomputer....yet!")

        async with message.channel.typing():
            user_embedding = gpt_embed(message.content)
            similar_embeddings = await query_pinecone(user_embedding, top_k=5)

            assistant_messages = []
            for metadata in similar_embeddings:
                assistant_message = f"This information will help me answer your query: {metadata['text']}"
                assistant_messages.append({'role': 'assistant', 'content': assistant_message})
            
            self.conversations[user_id].extend(assistant_messages)

            for attempt in range(30):
                try:
                    logger.info("Starting OpenAI call")
                    async with self.api_semaphore:
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
                        await self.send_message_safe("Sorry the API is a bit jammed up, hold tight and try again soon. Thanks human.")
                        return
                    elif 'rate limit' in str(e):
                        await asyncio.sleep(60)
                    else:
                        await asyncio.sleep(1)

        assistant_reply = response['choices'][0]['message']['content']
        self.conversations[user_id].append({
            'role': 'assistant',
            'content': assistant_reply,
        })

        if user_id in self.last_bot_messages:
            last_bot_message = self.last_bot_messages[user_id]
            await last_bot_message.edit(view=None)

        new_view = nextcord.ui.View()
        new_view.add_item(EndConversationButton(self, user_id))
        new_view.add_item(EndWithoutSaveButton(self, user_id))
        new_bot_message = await self.send_message_safe(message.channel.send(assistant_reply, view=new_view))

        self.last_bot_messages[user_id] = new_bot_message

        await thinking_message.delete()

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
            if user_id in self.models:
                del self.models[user_id]
            if user_id in self.last_bot_messages:
                del self.last_bot_messages[user_id]
            if user_id in self.chat_uuids:
                del self.chat_uuids[user_id]
            del self.threads[thread.id]

def setup(bot):
    bot.add_cog(ChatCog(bot))

