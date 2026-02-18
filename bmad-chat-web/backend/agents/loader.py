import os
import re
import yaml
from config import BMAD_AGENTS_PATH

def load_agents():
    """加载所有 BMad 角色"""
    agents = []

    if not os.path.exists(BMAD_AGENTS_PATH):
        return agents

    for filename in os.listdir(BMAD_AGENTS_PATH):
        if filename.endswith('.md'):
            filepath = os.path.join(BMAD_AGENTS_PATH, filename)
            agent = load_agent(filepath)
            if agent:
                agents.append(agent)

    return agents

def load_agent(filepath):
    """加载单个角色文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取 YAML 块
        yaml_match = re.search(r'```yaml\n(.*?)```', content, re.DOTALL)
        if not yaml_match:
            return None

        yaml_content = yaml_match.group(1)
        data = yaml.safe_load(yaml_content)

        if not data:
            return None

        return {
            'id': data.get('agent', {}).get('id', ''),
            'name': data.get('agent', {}).get('name', ''),
            'title': data.get('agent', {}).get('title', ''),
            'icon': data.get('agent', {}).get('icon', ''),
            'whenToUse': data.get('agent', {}).get('whenToUse', ''),
            'persona': data.get('persona', {}),
            'commands': data.get('commands', []),
            'core_principles': data.get('persona', {}).get('core_principles', []),
            'style': data.get('persona', {}).get('style', ''),
            'role': data.get('persona', {}).get('role', ''),
            'focus': data.get('persona', {}).get('focus', ''),
        }

    except Exception as e:
        print(f"Error loading agent from {filepath}: {e}")
        return None

def get_agent_by_id(agent_id):
    """根据 ID 获取角色"""
    agents = load_agents()
    for agent in agents:
        if agent['id'] == agent_id:
            return agent
    return None
