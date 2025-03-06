import nltk  # Natural Language Toolkit for NLP
import os  # OS module to interact with the file system

def download_stopwords():
    # Checking if stopwords are already downloaded in the system
    nltk_data_path = os.path.expanduser("~") + "/nltk_data"  # Get the user's home directory path for NLTK data
    
    # If the stopwords directory does not exist, download the stopwords dataset
    if not os.path.exists(nltk_data_path + "/corpora/stopwords"):
        nltk.download("stopwords", download_dir=nltk_data_path)  # Download stopwords to the specified directory
    
    # Set the nltk data path (prevents re-downloading by ensuring nltk looks here first)
    nltk.data.path.append(nltk_data_path)  
