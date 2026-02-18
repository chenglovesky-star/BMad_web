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
