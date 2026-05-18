import { useState } from "react";
import axios from "axios";

function App() {
  const [formData, setFormData] = useState({
    user_name: "",
    user_address: "",
    query: "",
    reference_number: "",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleSubmit = async () => {
    if (!formData.user_name || !formData.user_address || !formData.query) {
      setError("Please fill all required fields!");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const payload = {
        query: formData.reference_number
          ? `${formData.query} (Reference/Application No: ${formData.reference_number})`
          : formData.query,
        user_name: formData.user_name,
        user_address: formData.user_address,
      };
      const response = await axios.post(
        "http://127.0.0.1:8000/generate-rti",
        payload
      );
      setResult(response.data);
    } catch (err) {
      setError("Something went wrong. Make sure FastAPI is running!");
    }
    setLoading(false);
  };

  const handleReset = () => {
    setResult(null);
    setCopied(false);
    setFormData({ user_name: "", user_address: "", query: "", reference_number: "" });
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(result.draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={styles.page}>
      <div style={styles.container}>

        {/* Header */}
        <div style={styles.header}>
          <div style={styles.headerBadge}>RTI Act 2005</div>
          <h1 style={styles.headerTitle}>RTI Assistant</h1>
          <p style={styles.headerSub}>
            File your Right to Information application in seconds — free, fast, AI-powered
          </p>
        </div>

        {/* Form */}
        {!result && (
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>Tell us your problem</h2>

            <label style={styles.label}>Your Full Name <span style={styles.required}>*</span></label>
            <input
              style={styles.input}
              placeholder="e.g. Rahul Sharma"
              value={formData.user_name}
              onChange={(e) => setFormData({ ...formData, user_name: e.target.value })}
            />

            <label style={styles.label}>Your Address <span style={styles.required}>*</span></label>
            <input
              style={styles.input}
              placeholder="e.g. Andheri, Mumbai, Maharashtra"
              value={formData.user_address}
              onChange={(e) => setFormData({ ...formData, user_address: e.target.value })}
            />

            <label style={styles.label}>
              Reference / Application Number
              <span style={styles.optional}> (optional)</span>
            </label>
            <input
              style={styles.input}
              placeholder="e.g. PSK/MUM/2025/123456"
              value={formData.reference_number}
              onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
            />

            <label style={styles.label}>Describe your problem <span style={styles.required}>*</span></label>
            <textarea
              style={styles.textarea}
              placeholder="e.g. My passport application has been pending for 8 months in Mumbai and I have received no update"
              value={formData.query}
              onChange={(e) => setFormData({ ...formData, query: e.target.value })}
            />

            {error && <p style={styles.error}>⚠️ {error}</p>}

            <button
              style={loading ? styles.btnDisabled : styles.btn}
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? "⏳ Generating RTI... please wait (5-10 sec)" : "Generate RTI Application →"}
            </button>
          </div>
        )}

        {/* Result */}
        {result && (
          <div>
            <div style={styles.successBanner}>
              ✅ RTI Application Generated Successfully!
            </div>

            {/* Authority */}
            <div style={styles.card}>
              <h2 style={styles.cardTitle}>🏛️ Government Office Details</h2>
              {[
                ["Department", result.authority.department],
                ["PIO Name", result.authority.pio_name],
                ["Address", result.authority.address],
                ["Application Fee", `Rs. ${result.authority.fee}/-`],
                ["Level", result.authority.level],
              ].map(([label, value]) => (
                <div key={label} style={styles.infoRow}>
                  <span style={styles.infoLabel}>{label}</span>
                  <span style={styles.infoValue}>{value}</span>
                </div>
              ))}
              <div style={styles.infoRow}>
                <span style={styles.infoLabel}>Response Deadline</span>
                <span style={{ ...styles.infoValue, color: "#e53e3e", fontWeight: "700" }}>
                  {result.tracker.deadline_date} ({result.tracker.days_remaining} days left)
                </span>
              </div>
            </div>

            {/* RTI Letter */}
            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <h2 style={styles.cardTitle}>📄 Your RTI Application</h2>
                <button
                  style={copied ? styles.copiedBtn : styles.copyBtn}
                  onClick={handleCopy}
                >
                  {copied ? "✅ Copied!" : "📋 Copy"}
                </button>
              </div>
              <div style={styles.disclaimer}>
                ⚠️ This is an informational draft only. Please verify details before filing.
              </div>
              <pre style={styles.letterBox}>{result.draft}</pre>
            </div>

            {/* Quality Check */}
            <div style={styles.card}>
              <h2 style={styles.cardTitle}>✅ Quality Check</h2>
              <div style={styles.qualityRow}>
                <span style={{ color: "#38a169", fontWeight: "600" }}>
                  {result.review.message}
                </span>
                <span style={styles.wordCount}>
                  {result.review.word_count} / {result.review.max_words} words
                </span>
              </div>
              <div style={styles.progressBar}>
                <div
                  style={{
                    ...styles.progressFill,
                    width: `${Math.min((result.review.word_count / result.review.max_words) * 100, 100)}%`,
                    background: result.review.word_count > 400 ? "#e53e3e" : "#38a169",
                  }}
                />
              </div>
              <div style={styles.checksGrid}>
                {Object.entries(result.review.checks).map(([key, val]) => (
                  <div key={key} style={styles.checkRow}>
                    <span>{val ? "✅" : "❌"}</span>
                    <span style={styles.checkLabel}>{key.replace(/_/g, " ")}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Buttons */}
            <div style={styles.btnRow}>
              <button style={styles.btn} onClick={() => window.print()}>
                🖨️ Print / Save as PDF
              </button>
              <button style={styles.btnOutline} onClick={handleReset}>
                📝 File Another RTI
              </button>
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={styles.footer}>
          <p style={styles.footerMain}>
            Built with Agentic AI (FastAPI + Groq) | RTI Act 2005
          </p>
          <p style={styles.footerSub}>
            This tool is for informational purposes only and does not constitute legal advice.
            Always verify information before filing.
            Application fee of Rs.10/- applies for all RTI filings.
          </p>
        </div>

      </div>
    </div>
  );
}

const styles = {
  page: { background: "#f0f4f8", minHeight: "100vh", padding: "20px 16px" },
  container: { maxWidth: 720, margin: "0 auto", fontFamily: "'Segoe UI', sans-serif" },
  header: { background: "linear-gradient(135deg, #1a365d, #2b6cb0)", borderRadius: 16, padding: "36px 28px", marginBottom: 24, textAlign: "center" },
  headerBadge: { display: "inline-block", background: "rgba(255,255,255,0.15)", color: "#fff", fontSize: 11, fontWeight: "700", padding: "4px 12px", borderRadius: 20, marginBottom: 12, letterSpacing: "0.08em" },
  headerTitle: { color: "#fff", fontSize: 32, fontWeight: "800", margin: "0 0 8px" },
  headerSub: { color: "rgba(255,255,255,0.8)", fontSize: 14, margin: 0, lineHeight: 1.6 },
  card: { background: "#fff", borderRadius: 14, padding: "24px 28px", marginBottom: 20, boxShadow: "0 2px 12px rgba(0,0,0,0.07)" },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  cardTitle: { fontSize: 17, fontWeight: "700", color: "#1a365d", margin: 0 },
  label: { display: "block", fontSize: 13, fontWeight: "600", color: "#2d3748", marginBottom: 6, marginTop: 4 },
  required: { color: "#e53e3e" },
  optional: { color: "#a0aec0", fontWeight: "400", fontSize: 12 },
  input: { width: "100%", padding: "10px 14px", borderRadius: 8, border: "1.5px solid #e2e8f0", fontSize: 14, marginBottom: 14, boxSizing: "border-box", outline: "none" },
  textarea: { width: "100%", padding: "10px 14px", borderRadius: 8, border: "1.5px solid #e2e8f0", fontSize: 14, marginBottom: 16, minHeight: 110, boxSizing: "border-box", resize: "vertical", fontFamily: "inherit" },
  btn: { flex: 1, padding: "13px", background: "linear-gradient(135deg, #1a365d, #2b6cb0)", color: "#fff", border: "none", borderRadius: 10, fontSize: 15, fontWeight: "700", cursor: "pointer" },
  btnDisabled: { width: "100%", padding: "13px", background: "#a0aec0", color: "#fff", border: "none", borderRadius: 10, fontSize: 15, fontWeight: "600", cursor: "not-allowed" },
  btnOutline: { flex: 1, padding: "13px", background: "#fff", color: "#2b6cb0", border: "2px solid #2b6cb0", borderRadius: 10, fontSize: 14, fontWeight: "700", cursor: "pointer" },
  btnRow: { display: "flex", gap: 12, marginBottom: 24 },
  copyBtn: { padding: "6px 14px", background: "#ebf8ff", color: "#2b6cb0", border: "1.5px solid #90cdf4", borderRadius: 8, fontSize: 13, fontWeight: "600", cursor: "pointer" },
  copiedBtn: { padding: "6px 14px", background: "#c6f6d5", color: "#22543d", border: "1.5px solid #9ae6b4", borderRadius: 8, fontSize: 13, fontWeight: "600", cursor: "pointer" },
  error: { color: "#c53030", fontSize: 13, background: "#fff5f5", padding: "10px 14px", borderRadius: 8, marginBottom: 12 },
  successBanner: { background: "#c6f6d5", color: "#22543d", padding: "14px 20px", borderRadius: 10, marginBottom: 16, fontWeight: "700", textAlign: "center", fontSize: 15 },
  infoRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", padding: "10px 0", borderBottom: "1px solid #f7fafc" },
  infoLabel: { color: "#718096", fontSize: 13, minWidth: 120 },
  infoValue: { color: "#1a365d", fontSize: 13, fontWeight: "600", textAlign: "right", maxWidth: "65%" },
  disclaimer: { background: "#fffbeb", border: "1px solid #f6e05e", borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "#744210", marginBottom: 16, lineHeight: 1.6 },
  letterBox: { background: "#f7fafc", border: "1px solid #e2e8f0", borderRadius: 10, padding: "18px 20px", fontSize: 13, lineHeight: 1.8, whiteSpace: "pre-wrap", fontFamily: "'Courier New', monospace", margin: 0 },
  qualityRow: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 },
  wordCount: { fontSize: 12, color: "#718096", background: "#f7fafc", padding: "3px 10px", borderRadius: 20, border: "1px solid #e2e8f0" },
  progressBar: { height: 6, background: "#e2e8f0", borderRadius: 3, overflow: "hidden", marginBottom: 16 },
  progressFill: { height: "100%", borderRadius: 3, transition: "width 0.5s ease" },
  checksGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 },
  checkRow: { display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#4a5568" },
  checkLabel: { textTransform: "capitalize" },
  footer: { textAlign: "center", padding: "20px 0 30px", borderTop: "1px solid #e2e8f0", marginTop: 8 },
  footerMain: { fontSize: 13, fontWeight: "600", color: "#4a5568", margin: "0 0 6px" },
  footerSub: { fontSize: 11, color: "#a0aec0", lineHeight: 1.7, margin: 0, maxWidth: 500, marginLeft: "auto", marginRight: "auto" },
};

export default App;