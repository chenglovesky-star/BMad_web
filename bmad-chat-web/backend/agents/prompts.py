def build_system_prompt(agent):
    """根据角色定义构建 system prompt"""

    persona = agent.get('persona', {})
    core_principles = agent.get('core_principles', [])
    commands = agent.get('commands', [])

    prompt = f"""你是 {agent['name']}，{agent['title']}。

## 角色定义
{persona.get('role', '')}

## 风格
{persona.get('style', '')}

## 身份
{persona.get('identity', '')}

## 关注点
{persona.get('focus', '')}

## 核心原则
"""
    for i, principle in enumerate(core_principles, 1):
        prompt += f"{i}. {principle}\n"

    prompt += """
## 可用命令
"""
    for cmd in commands:
        if isinstance(cmd, dict):
            for key, value in cmd.items():
                prompt += f"- *{key}: {value}\n"
        else:
            prompt += f"- *{cmd}\n"

    prompt += f"""
## 使用场景
{agent.get('whenToUse', '')}

请以 {agent['name']} 的身份与用户交流。回答问题，执行命令，并在适当时候提供专业建议。
"""

    return prompt
