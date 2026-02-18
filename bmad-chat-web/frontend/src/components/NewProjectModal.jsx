import { useState } from 'react'

function NewProjectModal({ onClose, onCreate }) {
  const [name, setName] = useState('')
  const [path, setPath] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!name.trim() || !path.trim()) return
    onCreate(name.trim(), path.trim())
  }

  const handlePathChange = (e) => {
    // 处理用户输入的路径
    let value = e.target.value
    // 替换反斜杠为正斜杠
    value = value.replace(/\\/g, '/')
    setPath(value)

    // 如果项目名称为空，自动从路径提取
    if (!name) {
      const parts = value.split('/')
      const folderName = parts[parts.length - 1] || parts[parts.length - 2]
      if (folderName) {
        setName(folderName)
      }
    }
  }

  const handleNameChange = (e) => {
    setName(e.target.value)
    // 如果路径为空，自动生成路径
    if (!path && e.target.value) {
      const homePath = '/Users/apple/Desktop'
      setPath(`${homePath}/${e.target.value}`)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>新建项目</h2>
        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>项目名称</label>
            <input
              type="text"
              value={name}
              onChange={handleNameChange}
              placeholder="例如：我的第一个项目"
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>工作路径</label>
            <input
              type="text"
              value={path}
              onChange={handlePathChange}
              placeholder="/Users/apple/Desktop/我的项目"
            />
          </div>
          <div className="modal-buttons">
            <button type="button" className="cancel-btn" onClick={onClose}>
              取消
            </button>
            <button type="submit" className="create-btn" disabled={!name.trim() || !path.trim()}>
              创建
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default NewProjectModal
