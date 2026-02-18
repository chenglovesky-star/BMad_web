import { useState, useRef, useEffect } from 'react'

function ChatWindow({ messages, onSendMessage, loading }) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    onSendMessage(input.trim())
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="chat-window">
      <div className="messages">
        {/* 欢迎消息 */}
        {messages.length === 0 && (
          <div className="message assistant">
            <div className="message-header">
              <span>🤖</span>
              <span>Claude CLI</span>
            </div>
            你好！我是 Claude CLI，有什么我可以帮你的吗？
          </div>
        )}

        {/* 历史消息 */}
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            {msg.role === 'assistant' && (
              <div className="message-header">
                <span>🤖</span>
                <span>Claude CLI</span>
              </div>
            )}
            {msg.content}
          </div>
        ))}

        {/* 加载中 */}
        {loading && (
          <div className="message assistant">
            <div className="message-header">
              <span>🤖</span>
              <span>Claude CLI</span>
            </div>
            <div className="typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-area" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="向 Claude CLI 提问..."
          disabled={loading}
        />
        <button type="submit" disabled={!input.trim() || loading}>
          发送
        </button>
      </form>
    </div>
  )
}

export default ChatWindow
