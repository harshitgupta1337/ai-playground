// src/App.js
import React, { useState, useEffect } from "react";
import axios from "axios";
import { v4 as uuidv4 } from "uuid"; // npm install uuid

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [threadId, setThreadId] = useState("");

  // Generate thread ID on first load
  useEffect(() => {
    let tid = sessionStorage.getItem("thread_id");
    if (!tid) {
      tid = uuidv4();
      sessionStorage.setItem("thread_id", tid);
    }
    setThreadId(tid);
  }, []);

  const askAI = async () => {
    try {
      const res = await axios.post("http://10.0.0.35:8000/chat", {
        thread_id: threadId,
        question,
      });
      setAnswer(res.data.answer);
    } catch (err) {
      console.error("Error querying backend", err);
      setAnswer("Error contacting AI.");
    }
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h2>LangChain Chat</h2>
      <textarea
        value={question}
        onChange={e => setQuestion(e.target.value)}
        rows={4}
        style={{ width: "100%" }}
      />
      <br />
      <button onClick={askAI} style={{ marginTop: "1rem" }}>
        Ask
      </button>
      <h3>Response:</h3>
      <p>{answer}</p>
    </div>
  );
}

export default App;

