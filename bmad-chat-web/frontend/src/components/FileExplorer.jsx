import { useState } from 'react'

function FileExplorer({ files, onRefresh, onFileClick }) {
  const [expandedDirs, setExpandedDirs] = useState({})

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    const iconMap = {
      // JavaScript/TypeScript
      js: '🟨',
      jsx: '⚛️',
      ts: '🔷',
      tsx: '⚛️',
      mjs: '🟨',
      cjs: '🟨',

      // Python
      py: '🐍',
      pyw: '🐍',

      // Web
      html: '🌐',
      htm: '🌐',
      css: '🎨',
      scss: '🎨',
      sass: '🎨',
      less: '🎨',

      // Data/Config
      json: '📋',
      yaml: '⚙️',
      yml: '⚙️',
      toml: '⚙️',
      ini: '⚙️',
      conf: '⚙️',
      config: '⚙️',

      // Documents
      md: '📝',
      markdown: '📝',
      txt: '📄',
      doc: '📄',
      docx: '📄',
      pdf: '📕',

      // Images
      png: '🖼️',
      jpg: '🖼️',
      jpeg: '🖼️',
      gif: '🖼️',
      svg: '🖼️',
      webp: '🖼️',
      ico: '🖼️',

      // Code
      java: '☕',
      kt: '🟣',
      swift: '🍎',
      go: '🐹',
      rs: '🦀',
      cpp: '🔵',
      c: '🔵',
      h: '🔵',
      hpp: '🔵',
      cs: '🟠',
      rb: '💎',
      php: '🐘',
      scala: '🟢',
      dart: '🔵',

      // Build/Tools
      gradle: '🟢',
      maven: '🟠',
      npm: '📦',
      yarn: '📦',
      pnpm: '📦',

      // Other
      gitignore: '🔒',
      env: '🔐',
      lock: '🔐',
      xml: '📰',
      sh: '💻',
      bat: '💻',
      sql: '🗃️',
      dockerfile: '🐳',
      makefile: '🔧'
    }
    return iconMap[ext] || '📄'
  }

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const toggleDir = (path) => {
    setExpandedDirs(prev => ({
      ...prev,
      [path]: !prev[path]
    }))
  }

  const renderFileTree = (items, level = 0) => {
    return items.map((file, index) => (
      <div key={file.path + index} style={{ marginLeft: level * 12 }}>
        <div
          className={`file-item ${file.type === 'directory' ? 'directory' : ''}`}
          onClick={() => {
            if (file.type === 'directory') {
              toggleDir(file.path)
            } else if (onFileClick) {
              onFileClick(file)
            }
          }}
        >
          {file.type === 'directory' ? (
            <>
              <span className="file-icon">
                {expandedDirs[file.path] ? '📂' : '📁'}
              </span>
              <span className="file-name">{file.name}</span>
              <span className="file-meta">
                {file.modified && `· ${file.modified}`}
              </span>
            </>
          ) : (
            <>
              <span className="file-icon">{getFileIcon(file.name)}</span>
              <span className="file-name">{file.name}</span>
              <span className="file-meta">
                {file.size > 0 && formatSize(file.size)}
              </span>
            </>
          )}
        </div>
        {file.type === 'directory' && expandedDirs[file.path] && file.children && (
          <div className="file-children">
            {renderFileTree(file.children, level + 1)}
          </div>
        )}
      </div>
    ))
  }

  return (
    <div className="file-explorer">
      <h3>
        <span>📁 文件浏览器</span>
        <button className="refresh-btn" onClick={onRefresh}>🔄</button>
      </h3>
      <div className="file-tree">
        {files.length === 0 ? (
          <p style={{ color: '#999', fontSize: '13px', padding: '8px' }}>
            暂无文件，请先创建项目
          </p>
        ) : (
          renderFileTree(files)
        )}
      </div>
    </div>
  )
}

export default FileExplorer
