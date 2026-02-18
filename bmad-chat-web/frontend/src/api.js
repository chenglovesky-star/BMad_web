const API_BASE = '/api';

export async function fetchAgents() {
  const res = await fetch(`${API_BASE}/agents`);
  return res.json();
}

export async function fetchProjects() {
  const res = await fetch(`${API_BASE}/projects`);
  return res.json();
}

export async function createProject(name, path) {
  const res = await fetch(`${API_BASE}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, path })
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.error || '创建项目失败');
  }
  return res.json();
}

export async function deleteProject(projectId) {
  const res = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: 'DELETE'
  });
  return res.json();
}

export async function fetchProjectFiles(projectId, recursive = true) {
  const res = await fetch(`${API_BASE}/projects/${projectId}/files?recursive=${recursive}`);
  return res.json();
}

export async function sendChat(projectId, agentId, message, history) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ projectId, agentId, message, history })
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.error || '发送消息失败');
  }
  return res.json();
}

export async function sendChatStream(projectId, agentId, message, history) {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ projectId, agentId, message, history })
  });
  return res.body;
}

export async function readFile(filePath) {
  const encodedPath = encodeURIComponent(filePath);
  const res = await fetch(`${API_BASE}/files/read?path=${encodedPath}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.error || '读取文件失败');
  }
  return res.json();
}

export async function startClaude(mode = 'local', workingDir = null) {
  const res = await fetch(`${API_BASE}/claude/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode, workingDir })
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.error || '启动 Claude CLI 失败');
  }
  return res.json();
}

export async function sendClaudeChat(message, workingDir = null) {
  const res = await fetch(`${API_BASE}/claude/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, workingDir })
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.error || '发送消息失败');
  }
  return res.json();
}

export async function stopClaude() {
  const res = await fetch(`${API_BASE}/claude/stop`, {
    method: 'POST'
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.error || '停止 Claude CLI 失败');
  }
  return res.json();
}

export async function getClaudeStatus() {
  const res = await fetch(`${API_BASE}/claude/status`);
  return res.json();
}
