import { useState, useEffect } from 'react'
import { fetchAgents, fetchProjects, createProject, fetchProjectFiles, readFile, startClaude, sendClaudeChat, getClaudeStatus } from './api'
import FileExplorer from './components/FileExplorer'
import ChatWindow from './components/ChatWindow'
import NewProjectModal from './components/NewProjectModal'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function App() {
  const [agents, setAgents] = useState([])
  const [projects, setProjects] = useState([])
  const [currentProject, setCurrentProject] = useState(null)
  const [files, setFiles] = useState([])
  const [messages, setMessages] = useState([])
  const [showNewProject, setShowNewProject] = useState(false)
  const [loading, setLoading] = useState(false)
  const [previewFile, setPreviewFile] = useState(null)
  const [previewContent, setPreviewContent] = useState(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [claudeReady, setClaudeReady] = useState(false)
  const [claudeStatus, setClaudeStatus] = useState(null)

  // 加载角色和项目
  useEffect(() => {
    loadAgents()
    loadProjects()
    initClaude()
  }, [])

  // 当项目变化时加载文件
  useEffect(() => {
    if (currentProject) {
      loadFiles(currentProject.id)
    }
  }, [currentProject])

  async function initClaude() {
    try {
      const status = await startClaude('local')
      setClaudeReady(status.status === 'ready')
      setClaudeStatus(status)
    } catch (e) {
      console.error('Claude CLI 启动失败:', e)
    }
  }

  async function loadAgents() {
    const data = await fetchAgents()
    setAgents(data)
  }

  async function loadProjects() {
    const data = await fetchProjects()
    setProjects(data)
    if (data.length > 0) {
      setCurrentProject(data[0])
    }
  }

  async function loadFiles(projectId) {
    const data = await fetchProjectFiles(projectId)
    setFiles(data)
  }

  async function handleFileClick(file) {
    setPreviewFile(file)
    setPreviewLoading(true)
    try {
      const content = await readFile(file.path)
      setPreviewContent(content)
    } catch (error) {
      alert('读取文件失败: ' + error.message)
      setPreviewFile(null)
    } finally {
      setPreviewLoading(false)
    }
  }

  function closePreview() {
    setPreviewFile(null)
    setPreviewContent(null)
  }

  async function handleCreateProject(name, path) {
    try {
      const project = await createProject(name, path)
      project.conversations = []
      setProjects([...projects, project])
      setCurrentProject(project)
      setMessages([])
      setShowNewProject(false)
    } catch (error) {
      console.error('Error creating project:', error)
      alert('创建项目失败: ' + error.message)
    }
  }

  async function handleSendMessage(content) {
    if (!claudeReady) {
      alert('Claude CLI 未就绪')
      return
    }

    setLoading(true)

    try {
      const userMsg = { role: 'user', content }
      setMessages(prev => [...prev, userMsg])

      const response = await sendClaudeChat(content, currentProject?.path)

      const aiMsg = { role: 'assistant', content: response.reply }
      setMessages(prev => [...prev, aiMsg])

      if (currentProject) {
        loadFiles(currentProject.id)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      alert('发送消息失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <h1>BMad AI 助手</h1>
        </div>
        <div className="header-center">
          {/* 项目选择 */}
          <select
            className="project-select"
            value={currentProject?.id || ''}
            onChange={(e) => {
              const p = projects.find(p => p.id === e.target.value)
              setCurrentProject(p)
              setMessages([])
            }}
          >
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>

          {/* Claude CLI 状态 */}
          <div className={`claude-status ${claudeReady ? 'ready' : 'not-ready'}`}>
            {claudeReady ? '✓ Claude CLI 就绪' : '⏳ 初始化中...'}
          </div>
        </div>
        <div className="header-right">
          <button className="new-project-btn" onClick={() => setShowNewProject(true)}>
            + 新建项目
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {/* 左侧：文件浏览器 */}
        <aside className="sidebar">
          <FileExplorer
            files={files}
            onRefresh={() => currentProject && loadFiles(currentProject.id)}
            onFileClick={handleFileClick}
          />
        </aside>

        {/* 右侧：聊天窗口 */}
        <section className="chat-section">
          <ChatWindow
            messages={messages}
            onSendMessage={handleSendMessage}
            loading={loading}
          />
        </section>
      </main>

      {/* 新建项目弹窗 */}
      {showNewProject && (
        <NewProjectModal
          onClose={() => setShowNewProject(false)}
          onCreate={handleCreateProject}
        />
      )}

      {/* 文件预览弹窗 */}
      {previewFile && (
        <div className="modal-overlay" onClick={closePreview}>
          <div className="modal file-preview-modal" onClick={(e) => e.stopPropagation()}>
            <div className="preview-header">
              <h3>{previewFile.name}</h3>
              <button className="close-btn" onClick={closePreview}>×</button>
            </div>
            <div className="preview-content">
              {previewLoading ? (
                <div className="loading">加载中...</div>
              ) : previewContent ? (
                previewContent.ext === 'md' || previewContent.name.endsWith('.md') ? (
                  <div className="markdown-preview">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {previewContent.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <pre><code>{previewContent.content}</code></pre>
                )
              ) : (
                <div className="error">无法预览此文件</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
