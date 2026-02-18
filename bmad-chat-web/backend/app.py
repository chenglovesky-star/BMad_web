import os
import json
import time
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
from anthropic.types import ToolUseBlock
from agents.loader import load_agents, get_agent_by_id
from agents.prompts import build_system_prompt
from store import store
from config import ANTHROPIC_BASE_URL, ANTHROPIC_API_KEY, MODEL_NAME
from claude.cli_discovery import get_claude_cli_path

app = Flask(__name__)
CORS(app)

# 初始化 Anthropic 客户端
client = Anthropic(
    base_url=ANTHROPIC_BASE_URL,
    api_key=ANTHROPIC_API_KEY
)

# Claude CLI 会话管理器
claude_session_id = None

# 定义工具列表
TOOLS = [
    {
        "name": "write_file",
        "description": "写入内容到指定文件。如果文件不存在则创建，如果文件已存在则覆盖内容。",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径，例如: /Users/apple/project/test.md"},
                "content": {"type": "string", "description": "要写入的文件内容"}
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "读取指定文件的内容并返回。",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径，例如: /Users/apple/project/test.md"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "list_directory",
        "description": "列出指定目录下的所有文件和子目录。",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory_path": {"type": "string", "description": "目录路径"}
            },
            "required": ["directory_path"]
        }
    },
    {
        "name": "get_working_directory",
        "description": "获取当前工作目录的路径。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]


def execute_tool(tool_name, tool_input, project_path=None):
    """执行工具调用"""
    try:
        if tool_name == "write_file":
            file_path = tool_input.get("file_path")
            content = tool_input.get("content", "")

            # 安全检查：防止路径遍历
            if ".." in file_path:
                return {"error": "无效的路径"}

            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {"success": True, "message": f"文件已写入: {file_path}"}

        elif tool_name == "read_file":
            file_path = tool_input.get("file_path")

            # 安全检查
            if ".." in file_path:
                return {"error": "无效的路径"}

            if not os.path.exists(file_path):
                return {"error": "文件不存在"}

            if os.path.isdir(file_path):
                return {"error": "不能读取目录"}

            # 限制文件大小
            file_size = os.path.getsize(file_path)
            if file_size > 500 * 1024:
                return {"error": "文件太大，无法读取"}

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {"content": content, "size": file_size}

        elif tool_name == "list_directory":
            dir_path = tool_input.get("directory_path")

            if not os.path.exists(dir_path):
                return {"error": "目录不存在"}

            if not os.path.isdir(dir_path):
                return {"error": "不是有效的目录"}

            items = []
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file"
                })

            return {"items": items}

        elif tool_name == "get_working_directory":
            return {"path": project_path or os.getcwd()}

        else:
            return {"error": f"未知工具: {tool_name}"}

    except Exception as e:
        return {"error": str(e)}

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

@app.route('/api/files/read', methods=['GET'])
def read_file():
    """读取文件内容"""
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({'error': '文件路径不能为空'}), 400

    # 安全检查：防止路径遍历攻击（只检查 ..）
    if '..' in file_path:
        return jsonify({'error': '无效的路径'}), 400

    # 检查文件是否存在
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    if os.path.isdir(file_path):
        return jsonify({'error': '不能读取目录'}), 400

    # 限制文件大小（最大 500KB）
    file_size = os.path.getsize(file_path)
    if file_size > 500 * 1024:
        return jsonify({'error': '文件太大，无法预览'}), 400

    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 获取文件扩展名
        ext = os.path.splitext(file_path)[1].lstrip('.')

        return jsonify({
            'path': file_path,
            'name': os.path.basename(file_path),
            'ext': ext,
            'size': file_size,
            'content': content
        })
    except UnicodeDecodeError:
        return jsonify({'error': '无法读取二进制文件'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """发送聊天消息（支持工具调用）"""
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

    # 获取项目路径
    project = store.get_project(project_id)
    project_path = project.get('path') if project else None

    # 构建 system prompt
    system_prompt = build_system_prompt(agent)
    # 添加工具使用说明
    system_prompt += "\n\n你可以使用以下工具来帮助用户：\n"
    system_prompt += "- write_file: 写入文件\n"
    system_prompt += "- read_file: 读取文件\n"
    system_prompt += "- list_directory: 列出目录\n"
    system_prompt += "- get_working_directory: 获取当前工作目录\n"
    if project_path:
        system_prompt += f"\n当前工作目录: {project_path}\n"

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
        # 最多进行 5 轮工具调用
        max_iterations = 5
        for iteration in range(max_iterations):
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=TOOLS
            )

            # 检查是否有工具调用
            tool_uses = []
            text_content = []

            for block in response.content:
                if hasattr(block, 'type') and block.type == 'tool_use':
                    tool_uses.append(block)
                elif hasattr(block, 'text'):
                    text_content.append(block.text)

            # 如果没有工具调用，处理文本回复并结束
            if not tool_uses:
                reply = "".join(text_content)
                break

            # 处理工具调用
            for tool_use in tool_uses:
                tool_name = tool_use.name
                tool_input = tool_use.input
                tool_id = tool_use.id

                # 首先，将 AI 的工具调用作为助手消息添加到历史
                messages.append({
                    'role': 'assistant',
                    'content': [tool_use.model_dump()]
                })

                # 执行工具
                result = execute_tool(tool_name, tool_input, project_path)

                # 将工具结果添加到消息列表
                messages.append({
                    'role': 'user',
                    'content': [
                        {
                            'type': 'tool_result',
                            'tool_use_id': tool_id,
                            'content': json.dumps(result)
                        }
                    ]
                })

            # 继续循环，让 AI 根据工具结果生成回复

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


@app.route('/api/claude/start', methods=['POST'])
def start_claude():
    """启动 Claude CLI 会话（验证 CLI 可用性）"""
    from claude.cli_discovery import get_claude_cli_path

    cli_path = get_claude_cli_path()
    if not cli_path:
        return jsonify({'error': '未找到 Claude CLI'}), 404

    global claude_session_id
    claude_session_id = str(time.time())

    return jsonify({
        'sessionId': claude_session_id,
        'status': 'ready',
        'mode': 'print'
    })


@app.route('/api/claude/chat', methods=['POST'])
def claude_chat():
    """发送消息到 Claude CLI（使用 -p 模式）"""
    from claude.cli_discovery import get_claude_cli_path

    cli_path = get_claude_cli_path()
    if not cli_path:
        return jsonify({'error': '未找到 Claude CLI'}), 404

    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({'error': '消息不能为空'}), 400

    working_dir = data.get('workingDir')

    try:
        # 使用 -p 模式进行非交互式对话
        cmd = [str(cli_path), '-p', message]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=working_dir
        )

        reply = result.stdout if result.stdout else result.stderr

        return jsonify({
            'reply': reply,
            'sessionId': claude_session_id
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': '请求超时'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/claude/stop', methods=['POST'])
def stop_claude():
    """停止 Claude CLI 会话（无状态，直接返回）"""
    return jsonify({'status': 'stopped'})


@app.route('/api/claude/status', methods=['GET'])
def claude_status():
    """获取 Claude CLI 状态"""
    from claude.cli_discovery import get_claude_cli_path

    cli_path = get_claude_cli_path()
    if cli_path:
        return jsonify({
            'status': 'ready',
            'mode': 'print',
            'sessionId': claude_session_id,
            'cliPath': str(cli_path)
        })
    else:
        return jsonify({
            'status': 'not_found',
            'mode': None,
            'sessionId': None
        })


if __name__ == '__main__':
    app.run(debug=True, port=5001)
