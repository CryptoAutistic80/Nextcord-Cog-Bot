import os
import json
import re
import uuid
import aiohttp
import aiofiles
import PyPDF2
import nltk
import spacy
import openai
import numpy as np
import asyncio
import nextcord
from nextcord.ext import commands
import pinecone
from datetime import datetime
from modules.keywords import get_keywords
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

PINECONE_KEY = os.getenv("PINECONE_KEY")

class Administrator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        nltk.download('punkt')  # download the punkt tokenizer
        self.nlp = spacy.load('en_core_web_sm')  # initialize the nlp object here

    @commands.Cog.listener()
    async def on_ready(self):
        print("ADMIN HERE")

    def extract_text(self, pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            pages = []
            for page_num in range(len(pdf.pages)):
                page = pdf.pages[page_num]
                pages.append({'page_num': page_num+1, 'text': page.extract_text()})
        return pages

    def split_text_blocking(self, text):
        sentences = nltk.sent_tokenize(text)
        return ['\n'.join(sentences[i:i+8]) for i in range(0, len(sentences), 8)]

    async def split_text(self, text):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.split_text_blocking, text)

    def clean_text(self, text):
        text = text.encode('ascii', errors='ignore').decode('ascii')
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def gpt_embed_blocking(self, text):
        content = text.encode(encoding='ASCII', errors='ignore').decode()
        response = openai.Embedding.create(
            input=content,
            engine='text-embedding-ada-002'
        )
        vector = response['data'][0]['embedding']
        return vector

    async def gpt_embed(self, text):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.gpt_embed_blocking, text)

    def get_ner_keywords_blocking(self, text, num_keywords):
        doc = self.nlp(text)
        named_entities = [ent.text for ent in doc.ents if ent.label_ not in ['DATE', 'CARDINAL']]
        keywords_counter = Counter(named_entities)
        top_keywords = [word for word, _ in keywords_counter.most_common(num_keywords)]
        return top_keywords

    async def get_ner_keywords(self, text, num_keywords):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_ner_keywords_blocking, text, num_keywords)

    def get_tfidf_keywords_blocking(self, text, num_keywords):
        vectorizer = TfidfVectorizer(stop_words='english', max_features=num_keywords)
        vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        return list(feature_names)

    async def get_tfidf_keywords(self, text, num_keywords):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_tfidf_keywords_blocking, text, num_keywords)

    async def extract_keywords(self, text, num_keywords=4):
        cleaned_text = self.clean_text(text)

        ner_keywords = await self.get_ner_keywords(cleaned_text, num_keywords)
    
        tfidf_keywords = await self.get_tfidf_keywords(cleaned_text, num_keywords)

        keywords = ner_keywords + tfidf_keywords

        return keywords

    @nextcord.slash_command(description="Uploads the most recent PDF files sent by the user")
    async def pdf_upload(self, interaction: nextcord.Interaction, num_pdfs: int = 1):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer()

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

            if pdf_files:
                for pdf_file in pdf_files:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(pdf_file.url) as resp:
                            if resp.status == 200:
                                file_path = f'ai_resources/pdf_documents/{pdf_file.filename}'
                                async with aiofiles.open(file_path, 'wb') as f:
                                    await f.write(await resp.read())

                    pages = self.extract_text(file_path) # removed 'await'

                    embeddings = []
                    for page in pages:
                        page_num = page['page_num']
                        text = page['text']
                        page_groups = await self.split_text(text)
                        for i, group in enumerate(page_groups):
                            cleaned_text = self.clean_text(group)
                            metadata = {'filename': pdf_file.filename, 'file_number': i+1, 'page_number': page_num, 'uuid': str(uuid.uuid4()), 'text': cleaned_text}
            
                            keywords = await self.extract_keywords(cleaned_text)
                            metadata['keywords'] = keywords
            
                            vector = await self.gpt_embed(cleaned_text)
                            vector_np = np.array(vector)
                            embeddings.append((metadata['uuid'], vector_np))
            
                            output_filename = os.path.join('ai_resources/embeddings/', f'{metadata["uuid"]}.json')
                            async with aiofiles.open(output_filename, 'w') as f:
                                await f.write(json.dumps(metadata, indent=4))
            
                    batch_size = 100
                    pinecone.init(api_key=PINECONE_KEY, environment='us-east1-gcp')
                    pinecone_indexer = pinecone.Index("core-69")
                    loop = asyncio.get_event_loop()
                    for i in range(0, len(embeddings), batch_size):
                        batch = embeddings[i:i + batch_size]
                        await loop.run_in_executor(None, pinecone_indexer.upsert, [(unique_id, vector_np.tolist()) for unique_id, vector_np in batch], "library")

                await interaction.followup.send(f"{len(pdf_files)} PDF file(s) have been uploaded and processed successfully.", ephemeral=True)
            else:
                await interaction.followup.send("No recent PDF files found.", ephemeral=True)
        else:
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
