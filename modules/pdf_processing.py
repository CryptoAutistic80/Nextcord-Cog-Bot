import os
import re
from PyPDF2 import PdfReader
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

def get_keywords(text, num_top_keywords=10):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=num_top_keywords)
    vectorizer.fit_transform([text])

    # Get the feature names (keywords)
    feature_names = vectorizer.get_feature_names_out()

    # Return the keywords as metadata
    metadata = {
        "keywords": list(feature_names)
    }

    return metadata

def read_pdf(file_path):
    with open(file_path, 'rb') as pdf_file:
        pdf_reader = PdfReader(pdf_file)
        text_content = ''
        for page_num in range(len(pdf_reader.pages)):
            text_content += pdf_reader.pages[page_num].extract_text()
    return text_content


def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    text = text.lower()
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+[a-zA-Z]\s+', ' ', text)
    text = re.sub(r'\s+', ' ', text, flags=re.I)
    text = re.sub(r'^b\s+', '', text)
    tokenized_text = word_tokenize(text)
    text = ' '.join(word for word in tokenized_text if word not in stop_words)
    return text


def main():
    folder_path = 'ai_resources/pdf_docs'

    # Create the directory if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)

    preprocessed_text_content = ''
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.pdf'):
            file_path = os.path.join(folder_path, file_name)
            text_content = read_pdf(file_path)
            
            # Segment into sentences and preprocess each sentence
            sentences = sent_tokenize(text_content)
            preprocessed_sentences = [preprocess_text(sentence) for sentence in sentences]
            
            preprocessed_text_content += '\n'.join(preprocessed_sentences) + '\n'

    # Extract keywords
    metadata = get_keywords(preprocessed_text_content)
    print(f'Keywords: {", ".join(metadata["keywords"])}')

    with open('output.txt', 'w') as output_file:
        output_file.write(preprocessed_text_content)


if __name__ == '__main__':
    main()
