import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # API Keys (free tier)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Get from ai.google.dev
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    SOPS_DIR = os.path.join(DATA_DIR, 'sops')
    VECTOR_DB_DIR = os.path.join(DATA_DIR, 'vectordb')
    
    # Vector Store Settings
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Free, runs locally
    COLLECTION_NAME = 'tata_steel_sops'
    
    # Agent Settings
    MAX_CONTEXT_LENGTH = 4000
    TEMPERATURE = 0.7
    TOP_K_RESULTS = 3
    
    # Session Settings
    SESSION_TIMEOUT = 3600  # 1 hour
