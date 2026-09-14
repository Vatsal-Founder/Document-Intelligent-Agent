import { useState, useEffect } from "react";
import "./App.css";

const API = "https://document-intelligent-agent-1.onrender.com";

const AVATAR_COLORS = ["#6c5ce7", "#e67e22", "#16a085", "#e84393", "#0984e3", "#d35400"];

function avatarColor(id) {
  let hash = 0;
  for (const ch of id) hash = (hash * 31 + ch.charCodeAt(0)) % AVATAR_COLORS.length;
  return AVATAR_COLORS[hash];
}

function initials(name) {
  return name.split(" ").map((p) => p[0]).join("").slice(0, 2).toUpperCase();
}

function formatProductType(type) {
  return type.split("_")[0].replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatEmployment(type) {
  return type.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function suggestedQuestions(loan) {
  const base = [
    "Can I overpay without a penalty?",
    "What's my monthly payment?",
    "Is there an early repayment charge?",
  ];
  const last = loan.product_type.includes("variable")
    ? "How much notice do I get before a rate change?"
    : "Can I take a payment break?";
  return [...base, last];
}

function App() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [review, setReview] = useState(null);

  const [loans, setLoans] = useState([]);
  const [selectedLoan, setSelectedLoan] = useState(null);
  const [threadId, setThreadId] = useState(() => "web-" + Date.now());

  useEffect(() => {
    fetch(`${API}/loans`)
      .then((res) => res.json())
      .then(setLoans)
      .catch(() => setLoans([]));
  }, []);

  function selectLoan(loan) {
    if (loading) return;
    const next = selectedLoan?.loan_id === loan.loan_id ? null : loan;
    setSelectedLoan(next);
    setThreadId("web-" + Date.now());
    setHistory([]);
    setReview(null);
    setQuestion("");
  }

  async function handleSubmit(text) {
    const q = (text ?? question).trim();
    if (!q) return;
    setLoading(true);
    setReview(null);

    const contextPrefix = selectedLoan
      ? `[Loan ${selectedLoan.loan_id} — ${selectedLoan.customer_name}] `
      : "";

    setHistory((h) => [...h, { role: "user", text: q }]);
    setQuestion("");

    try {
      const res = await fetch(`${API}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: contextPrefix + q, thread_id: threadId }),
      });

      if (res.status === 429) {
        setHistory((h) => [...h, { role: "assistant", text: "You've hit the hourly limit for this demo — try again in a bit." }]);
      } else if (!res.ok) {
        setHistory((h) => [...h, { role: "assistant", text: "Error: could not reach the server." }]);
      } else {
        const data = await res.json();
        if (data.status === "needs_review") {
          setReview(data);
        } else {
          setHistory((h) => [...h, { role: "assistant", text: data.answer }]);
        }
      }
    } catch (e) {
      setHistory((h) => [...h, { role: "assistant", text: "Error: could not reach the server." }]);
    }
    setLoading(false);
  }

  async function handleDecision(decision) {
    setLoading(true);
    try {
      const res = await fetch(`${API}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId, decision }),
      });

      if (res.status === 429) {
        setHistory((h) => [...h, { role: "assistant", text: "You've hit the hourly limit for this demo — try again in a bit." }]);
      } else if (!res.ok) {
        setHistory((h) => [...h, { role: "assistant", text: "Error: could not reach the server." }]);
      } else {
        const data = await res.json();
        setHistory((h) => [...h, { role: "assistant", text: data.answer }]);
      }
      setReview(null);
    } catch (e) {
      setHistory((h) => [...h, { role: "assistant", text: "Error: could not reach the server." }]);
    }
    setLoading(false);
  }

  return (
    <div className="app">
      <div className="header">
        <h1>Document Intelligence Agent</h1>
        <p>Ask about loan agreements, balances, or repayment calculations.</p>
      </div>

      <div className="section-label">Demo customers: Pick one for context</div>
      <div className="loan-grid">
        {loans.map((loan) => (
          <button
            key={loan.loan_id}
            className={`loan-card ${selectedLoan?.loan_id === loan.loan_id ? "selected" : ""}`}
            onClick={() => selectLoan(loan)}
            disabled={loading}
          >
            <div className="loan-card-top" style={{ background: avatarColor(loan.loan_id) }} />
            <div className="loan-card-main">
              <div className="avatar" style={{ background: avatarColor(loan.loan_id) }}>
                {initials(loan.customer_name)}
              </div>
              <div className="loan-card-body">
                <div className="loan-card-name">{loan.customer_name}</div>
                <div className="loan-card-meta">
                  <span className="tag mono">{loan.loan_id}</span>
                  <span className="tag">{formatProductType(loan.product_type)}</span>
                </div>
                <div className="loan-card-meta">
                  <span className="tag">{loan.term_years} yr term</span>
                  <span className="tag">{formatEmployment(loan.employment_type)}</span>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="layout">
        <div>
          <div className="chat-panel">
            {history.length === 0 && (
              <div className="chat-empty">Pick a customer above, or just ask a question to get started.</div>
            )}
            {history.map((turn, i) => (
              <div key={i} className={`bubble-row ${turn.role}`}>
                <div className={`bubble ${turn.role}`}>{turn.text}</div>
              </div>
            ))}
            {loading && <div className="thinking">Thinking…</div>}
          </div>

          {review && (
            <div className="review-card">
              <div className="review-label">Needs human review</div>
              <p>{review.reason}</p>
              <p>{review.proposed_answer}</p>
              <div className="review-actions">
                <button className="btn btn-primary" onClick={() => handleDecision("yes")}>Approve</button>
                <button className="btn btn-outline" onClick={() => handleDecision("no")}>Reject</button>
              </div>
            </div>
          )}

          <div className="input-bar">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What is the outstanding balance?"
              rows={2}
            />
            <button className="btn btn-primary" onClick={() => handleSubmit()} disabled={loading}>
              {loading ? "…" : "Ask"}
            </button>
          </div>
        </div>

        <aside className="panel">
          {!selectedLoan && (
            <div className="panel-empty">Select a customer to see their details and suggested questions.</div>
          )}
          {selectedLoan && (
            <>
              <div className="panel-header">
                <div className="panel-avatar" style={{ background: avatarColor(selectedLoan.loan_id) }}>
                  {initials(selectedLoan.customer_name)}
                </div>
                <div>
                  <div className="panel-name">{selectedLoan.customer_name}</div>
                  <div className="panel-sub">{selectedLoan.loan_id}</div>
                </div>
              </div>

              <div className="panel-details">
                <div className="panel-row">
                  <span className="panel-row-label">Loan type</span>
                  <span className="panel-row-value">{formatProductType(selectedLoan.product_type)}</span>
                </div>
                <div className="panel-row">
                  <span className="panel-row-label">Term</span>
                  <span className="panel-row-value">{selectedLoan.term_years} years</span>
                </div>
                <div className="panel-row">
                  <span className="panel-row-label">Started</span>
                  <span className="panel-row-value">{selectedLoan.start_date}</span>
                </div>
                <div className="panel-row">
                  <span className="panel-row-label">Employment</span>
                  <span className="panel-row-value">{formatEmployment(selectedLoan.employment_type)}</span>
                </div>
              </div>

              <div className="panel-suggestions-label">Try asking</div>
              {suggestedQuestions(selectedLoan).map((q) => (
                <button key={q} className="suggestion-btn" onClick={() => handleSubmit(q)} disabled={loading}>
                  {q}
                </button>
              ))}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}

export default App;
