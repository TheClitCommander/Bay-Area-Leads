import spacy
import gensim
from gensim.models import Word2Vec
from pprint import pprint

def test_installations():
    print("Testing spaCy and gensim installations...")
    
    # Test spaCy
    print("\n1. Testing spaCy:")
    nlp = spacy.load("en_core_web_sm")
    text = "Beautiful 3-bedroom waterfront property with modern amenities in Portland, Maine. Listed at $750,000."
    doc = nlp(text)
    
    print("\nEntities found:")
    for ent in doc.ents:
        print(f"- {ent.text} ({ent.label_})")
    
    print("\nKey noun phrases:")
    for chunk in doc.noun_chunks:
        print(f"- {chunk.text}")
    
    # Test gensim
    print("\n2. Testing gensim:")
    sentences = [
        ["waterfront", "property", "beach", "view"],
        ["modern", "amenities", "luxury", "home"],
        ["real", "estate", "investment", "property"]
    ]
    
    model = Word2Vec(sentences, min_count=1)
    print("\nSimilar words to 'property':")
    try:
        similar_words = model.wv.most_similar("property", topn=2)
        for word, score in similar_words:
            print(f"- {word}: {score:.4f}")
    except KeyError:
        print("(Need more training data for meaningful similarities)")

if __name__ == "__main__":
    test_installations()
