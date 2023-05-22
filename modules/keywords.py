import spacy
from collections import Counter
import re

# Load a SpaCy model for NER (make sure to download it first)
nlp = spacy.load('en_core_web_sm')

# Define a regular expression pattern to exclude
pattern = re.compile(r'\b\d{1,2}(?:st|nd|rd|th)\b')

def get_keywords(conversation_history, num_top_keywords=10):
    # Extract the conversation content
    conversation_content = " ".join([message["content"] for message in conversation_history])

    # Apply NER and extract named entities of all types
    doc = nlp(conversation_content)
    named_entities = [ent.text for ent in doc.ents if not pattern.match(ent.text)]

    # Filter out duplicate named entities and count their occurrences
    keywords_counter = Counter(named_entities)

    # Retrieve the top keywords
    top_keywords = [word for word, _ in keywords_counter.most_common(num_top_keywords)]

    # Return the keywords as metadata
    metadata = {
        "keywords": top_keywords
    }

    return metadata
