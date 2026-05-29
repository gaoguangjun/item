import os

# LLM Configuration
LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-4o')

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'games.db')

# Flask
PORT = 5002
DEBUG = True

# Default user
DEFAULT_USERNAME = '玩家'

# Game categories
CATEGORIES = ['休闲', '动作', '益智', '射击', '策略', '冒险', '模拟', '体育']
