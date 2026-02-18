import os
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
from agents.loader import load_agents, get_agent_by_id
from agents.prompts import build_system_prompt
from store import store
from config import ANTHROPIC_BASE_URL, ANTHROPIC_API_KEY, MODEL_NAME

app = Flask(__name__)
CORS(app)

# 初始化 Anthropic 客户端
client = Anthropic(
    base_url=ANTHROPIC_BASE_URL,
    api_key=ANTHROPIC_API_KEY
)

# 会话存储（内存中）
sessions = {}

def get_file_info(path):
    """获取文件详细信息"""
    try:
        stat = os.stat(path)
        return {
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
            'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M')
        }
    except:
        return {'size': 0, 'modified': '', 'created': ''}

def get_file_tree(path, recursive=False, depth=0, max_depth=3):
    """获取目录的文件树结构"""
    items = []
    try:
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                children = []
                if recursive and depth < max_depth:
                    children = get_file_tree(item_path, recursive, depth + 1, max_depth)
                items.append({
                    'name': item,
                    'type': 'directory',
                    'path': item_path,
                    'children': children,
                    **get_file_info(item_path)
                })
            else:
                items.append({
                    'name': item,
                    'type': 'file',
                    'path': item_path,
                    **get_file_info(item_path)
                })
    except PermissionError:
        pass
    return items

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """获取可用角色列表"""
    agents = load_agents()
    return jsonify(agents)

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """获取项目列表"""
    projects = store.get_projects()
    return jsonify(projects)

@app.route('/api/projects', methods=['POST'])
def create_project():
    """新建项目"""
    data = request.json
    name = data.get('name')
    path = data.get('path')

    if not name or not path:
        return jsonify({'error': '名称和路径不能为空'}), 400

    # 创建目录
    os.makedirs(path, exist_ok=True)

    # 创建默认的 README.md 文件
    readme_path = os.path.join(path, 'README.md')
    if not os.path.exists(readme_path):
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {name}\n\n")
            f.write(f"项目路径: {path}\n\n")
            f.write("## 项目描述\n\n")
            f.write("在这里添加项目描述...\n\n")
            f.write("## 开始使用\n\n")
            f.write("1. \n2. \n3. \n")

    project = store.create_project(name, path)
    return jsonify(project)

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """获取项目详情"""
    project = store.get_project(project_id)
    if not project:
        return jsonify({'error': '项目不存在'}), 404
    return jsonify(project)

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    store.delete_project(project_id)
    return jsonify({'success': True})

@app.route('/api/projects/<project_id>/files', methods=['GET'])
def get_project_files(project_id):
    """获取项目的文件列表"""
    project = store.get_project(project_id)
    if not project:
        return jsonify({'error': '项目不存在'}), 404

    path = project.get('path')
    if not os.path.exists(path):
        return jsonify([])

    # 支持递归获取文件树
    recursive = request.args.get('recursive', 'false').lower() == 'true'
    files = get_file_tree(path, recursive=recursive)
    return jsonify(files)

@app.route('/api/chat', methods=['POST'])
def chat():
    """发送聊天消息"""
    data = request.json
    project_id = data.get('projectId')
    agent_id = data.get('agentId')
    message = data.get('message')
    history = data.get('history', [])

    if not project_id or not agent_id or not message:
        return jsonify({'error': '缺少必要参数'}), 400

    # 获取角色信息
    agent = get_agent_by_id(agent_id)
    if not agent:
        return jsonify({'error': '角色不存在'}), 404

    # 构建 system prompt
    system_prompt = build_system_prompt(agent)

    # 构建消息列表
    messages = []
    for msg in history:
        messages.append({
            'role': msg.get('role', 'user'),
            'content': msg.get('content', '')
        })
    messages.append({
        'role': 'user',
        'content': message
    })

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        )

        # 提取回复内容
        reply = ""
        for block in response.content:
            if hasattr(block, 'text'):
                reply += block.text

        # 保存对话到项目
        conversation = {
            'role': 'user',
            'content': message
        }
        store.add_conversation(project_id, conversation)
        conversation = {
            'role': 'assistant',
            'content': reply
        }
        store.add_conversation(project_id, conversation)

        return jsonify({
            'reply': reply,
            'usage': {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天"""
    data = request.json
    project_id = data.get('projectId')
    agent_id = data.get('agentId')
    message = data.get('message')
    history = data.get('history', [])

    if not project_id or not agent_id or not message:
        return jsonify({'error': '缺少必要参数'}), 400

    agent = get_agent_by_id(agent_id)
    if not agent:
        return jsonify({'error': '角色不存在'}), 404

    system_prompt = build_system_prompt(agent)

    messages = []
    for msg in history:
        messages.append({
            'role': msg.get('role', 'user'),
            'content': msg.get('content', '')
        })
    messages.append({
        'role': 'user',
        'content': message
    })

    def generate():
        try:
            with client.messages.stream(
                model=MODEL_NAME,
                max_tokens=4096,
                system=system_prompt,
                messages=messages
            ) as stream:
                for event in stream:
                    if hasattr(event, 'text') and event.text:
                        yield f"data: {json.dumps({'text': event.text})}\n\n"
                    elif hasattr(event, 'type'):
                        if event.type == 'message_stop':
                            # 保存对话
                            conversation = {'role': 'user', 'content': message}
                            store.add_conversation(project_id, conversation)
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return generate(), {'Content-Type': 'text/event-stream'}

if __name__ == '__main__':
    app.run(debug=True, port=5001)
