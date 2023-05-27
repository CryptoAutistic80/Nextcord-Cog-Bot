import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import asyncio
import concurrent.futures

# Load a SpaCy model for NER (make sure to download it first)
nlp = spacy.load('en_core_web_sm')

async def get_tfidf_keywords(conversation_content, num_top_keywords=10):
    # Initialize a TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words='english', max_features=num_top_keywords)

    # Fit the vectorizer and transform the conversation content into a TF-IDF matrix
    with concurrent.futures.ThreadPoolExecutor() as pool:
        await asyncio.get_event_loop().run_in_executor(pool, vectorizer.fit_transform, [conversation_content])

    # Get the feature names (keywords)
    feature_names = vectorizer.get_feature_names_out()

    return list(feature_names)

async def get_ner_keywords(conversation_content, num_top_keywords=10):
    # Apply NER and extract named entities of all types
    with concurrent.futures.ThreadPoolExecutor() as pool:
        doc = await asyncio.get_event_loop().run_in_executor(pool, nlp, conversation_content)
    named_entities = [ent.text for ent in doc.ents if ent.label_ not in ['DATE', 'CARDINAL']]

    # Filter out duplicate named entities and count their occurrences
    keywords_counter = Counter(named_entities)

    # Retrieve the top keywords
    top_keywords = [word for word, _ in keywords_counter.most_common(num_top_keywords)]

    return top_keywords

async def get_keywords(conversation_history, num_top_keywords=10):
    # Extract the conversation content
    conversation_content = " ".join([message["content"] for message in conversation_history])

    # Get TF-IDF keywords
    tfidf_keywords = await get_tfidf_keywords(conversation_content, num_top_keywords)

    # Get NER keywords
    ner_keywords = await get_ner_keywords(conversation_content, num_top_keywords)

    # Combine the keywords
    keywords = tfidf_keywords + ner_keywords

    # Return the keywords as metadata
    metadata = {
        "keywords": keywords
    }

    # Print the keywords
    print("Keywords:", keywords)

    return metadata



