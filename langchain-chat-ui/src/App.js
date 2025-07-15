import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { v4 as uuidv4 } from "uuid";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [threadId, setThreadId] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    let tid = sessionStorage.getItem("thread_id");
    if (!tid) {
      tid = uuidv4();
      sessionStorage.setItem("thread_id", tid);
    }
    setThreadId(tid);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post("http://174.168.62.145:8000/chat", {
        thread_id: threadId,
        question: input,
      });

      const botMessage = { role: "bot", text: res.data.answer };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "bot", text: "Error contacting server." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.chatBox}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              ...styles.message,
              ...(msg.role === "user" ? styles.userMessage : styles.botMessage),
            }}
          >
            {msg.text}
          </div>
        ))}

        {loading && (
          <div style={{ ...styles.message, ...styles.botMessage }}>
            <img
              src="https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif"
              alt="Thinking..."
              style={{ height: "40px" }}
            />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div style={styles.inputContainer}>
        <textarea
          style={styles.textarea}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          placeholder={loading ? "Thinking..." : "Type your message..."}
        />
        <button style={styles.button} onClick={handleSend} disabled={loading}>
          Ask
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    fontFamily: "Arial, sans-serif",
  },
  chatBox: {
    flex: 1,
    padding: "1rem",
    overflowY: "auto",
    overflowX: "hidden",      // 🔑 Prevent horizontal scroll
    background: "#f4f4f4",
    display: "flex",
    flexDirection: "column",
  },
  message: {
    maxWidth: "70%",
    padding: "0.6rem 1rem",
    borderRadius: "1rem",
    marginBottom: "0.5rem",
    lineHeight: 1.4,
    whiteSpace: "pre-wrap",      // Allows line breaks and wrapping
    wordBreak: "break-word",     // Wraps long words
    overflowWrap: "break-word",  // Fallback for older browsers
  },
  userMessage: {
    backgroundColor: "#007bff",
    color: "white",
    alignSelf: "flex-end",
    marginLeft: "auto",
  },
  botMessage: {
    backgroundColor: "#e4e6eb",
    color: "#111",
    alignSelf: "flex-start",
    marginRight: "auto",
  },
  inputContainer: {
    display: "flex",
    padding: "1rem",
    borderTop: "1px solid #ccc",
    backgroundColor: "white",
  },
  textarea: {
    flex: 1,
    resize: "none",
    padding: "0.75rem",
    fontSize: "1rem",
    borderRadius: "0.5rem",
    border: "1px solid #ccc",
    marginRight: "1rem",
    height: "3rem",
  },
  button: {
    padding: "0.75rem 1.5rem",
    backgroundColor: "#28a745",
    color: "white",
    border: "none",
    borderRadius: "0.5rem",
    cursor: "pointer",
  },
};

export default App;

