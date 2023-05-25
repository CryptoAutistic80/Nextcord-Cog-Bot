import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

# Load a SpaCy model for NER (make sure to download it first)
nlp = spacy.load('en_core_web_sm')

def get_tfidf_keywords(text, num_top_keywords=30):
    # Initialize a TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words='english', max_features=num_top_keywords)

    # Fit the vectorizer and transform the text into a TF-IDF matrix
    vectorizer.fit_transform([text])

    # Get the feature names (keywords)
    feature_names = vectorizer.get_feature_names_out()

    return list(feature_names)

def get_ner_keywords(text, num_top_keywords=30):
    # Apply NER and extract named entities of all types
    doc = nlp(text)
    named_entities = [ent.text for ent in doc.ents if ent.label_ not in ['DATE', 'CARDINAL']]

    # Filter out duplicate named entities and count their occurrences
    keywords_counter = Counter(named_entities)

    # Retrieve the top keywords
    top_keywords = [word for word, _ in keywords_counter.most_common(num_top_keywords)]

    return top_keywords

def get_keywords(text, num_top_keywords=30):
    # Get TF-IDF keywords
    tfidf_keywords = get_tfidf_keywords(text, num_top_keywords)

    # Get NER keywords
    ner_keywords = get_ner_keywords(text, num_top_keywords)

    # Combine the keywords
    keywords = tfidf_keywords + ner_keywords

    # Remove duplicates
    keywords = list(set(keywords))

    # Return the keywords as metadata
    metadata = {
        "keywords": keywords
    }

    # Print the keywords
    print("Keywords:", keywords)

    return metadata
