import os

# API 配置
ANTHROPIC_BASE_URL = "https://api.minimaxi.com/anthropic"
ANTHROPIC_API_KEY = "sk-cp-Mu2tAGd_P5c8JhIAsUOXa1X5ADePAp1emZXv9HQphv2XyxrMBYtYU1YbAaSm4GEJGyQilrKeqGPzWWW5pUmehULvvz1x4UfIthDKZlOIneerRFWXpEbaCUI"
MODEL_NAME = "MiniMax-M2.5"

# 数据存储路径
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
PROJECTS_FILE = os.path.join(DATA_DIR, 'projects.json')

# BMad agents 路径
BMAD_AGENTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.bmad-core', 'agents')
