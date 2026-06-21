import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { createClient } from "@supabase/supabase-js";

const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:8000";
const STATUSES = ["Pending", "Filed", "Response Received", "Appeal Needed", "Closed"];
const SAVED_PROFILE_KEY = "rti_assistant_profile";
const SUPABASE_URL = process.env.REACT_APP_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.REACT_APP_SUPABASE_ANON_KEY;
const supabase = SUPABASE_URL && SUPABASE_ANON_KEY
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;

function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const savedProfile = JSON.parse(localStorage.getItem(SAVED_PROFILE_KEY)) || null;
      return savedProfile?.user_key ? savedProfile : null;
    } catch {
      return null;
    }
  });
  const [loginData, setLoginData] = useState({
    user_key: "",
    password: "",
    confirm_password: "",
    user_name: "",
    user_address: "",
  });
  const [authMode, setAuthMode] = useState("signIn");
  const [activeView, setActiveView] = useState("generate");
  const [formData, setFormData] = useState({
    user_name: "",
    user_address: "",
    query: "",
    reference_number: "",
  });
  const [lookupName, setLookupName] = useState("");
  const [result, setResult] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [applications, setApplications] = useState([]);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const accountKey = currentUser?.user_key || "";
  const activeLookup = lookupName || accountKey;
  const displayName = currentUser?.user_name || formData.user_name;

  const agentSteps = useMemo(
  () => [
    ["Step 1: Reading your problem", "Understanding what you need help with"],
    ["Step 2: Identifying the issue", "Finding the subject, state, and department"],
    ["Step 3: Finding the right office", "Locating the correct government officer"],
    ["Step 4: Writing your application", "Preparing the RTI letter in legal format"],
    ["Step 5: Checking quality", "Verifying the application is complete"],
    ["Step 6: Saving your case", "Storing application and setting deadline"],
  ],
    []
  );

  const updateForm = (field, value) => {
    setFormData({ ...formData, [field]: value });
    if (field === "user_name") setLookupName(value);
  };

  useEffect(() => {
    if (!currentUser) return;
    setFormData((current) => ({
      ...current,
      user_name: currentUser.user_name,
      user_address: currentUser.user_address,
    }));
    setLookupName(currentUser.user_key);
  }, [currentUser]);

  const loadDashboard = useCallback(async (lookup = activeLookup) => {
    if (!lookup) return;
    setDashboardLoading(true);
    setError("");
    try {
      const [dashboardResponse, applicationsResponse] = await Promise.all([
        axios.get(`${API_BASE}/dashboard/${encodeURIComponent(lookup)}`),
        axios.get(`${API_BASE}/my-rtis/${encodeURIComponent(lookup)}`),
      ]);
      setDashboard(dashboardResponse.data.stats);
      setApplications(applicationsResponse.data.applications);
      setSelectedApplication(null);
    } catch (err) {
      setError("Could not load dashboard data. Please check the backend server.");
    }
    setDashboardLoading(false);
  }, [activeLookup]);

  const handleLoadLookup = async () => {
    if (!lookupName) {
      setError("Enter an email/mobile account ID to load records.");
      return;
    }
    await loadDashboard(lookupName);
    setActiveView("applications");
  };

  useEffect(() => {
    if (activeView !== "dashboard" && activeView !== "applications") return;
    if (!activeLookup) return;
    loadDashboard(activeLookup);
  }, [activeView, activeLookup, loadDashboard]);

  const handleSubmit = async () => {
    if (!formData.user_name || !formData.user_address || !formData.query) {
      setError("Please fill all required fields.");
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
        user_key: accountKey,
      };
      const response = await axios.post(`${API_BASE}/generate-rti`, payload);
      setResult(response.data);
      setLookupName(accountKey);
      await loadDashboard(accountKey);
    } catch (err) {
      setError("Could not connect to the backend. Please make sure FastAPI is running.");
    }

    setLoading(false);
  };

  const handleLogin = async (mode = "signIn") => {
    if (!loginData.user_key || !loginData.password) {
      setError("Please enter email and password to continue.");
      return;
    }
    if (mode === "signUp") {
      if (!loginData.confirm_password || !loginData.user_name || !loginData.user_address) {
        setError("Please enter email, password, confirm password, name, and address.");
        return;
      }
      if (loginData.password !== loginData.confirm_password) {
        setError("Password and confirm password do not match.");
        return;
      }
      if (loginData.password.length < 6) {
        setError("Password must be at least 6 characters.");
        return;
      }
    }
    if (!supabase) {
      setError("Supabase Auth is not configured. Check frontend .env values.");
      return;
    }

    setError("");

    const email = loginData.user_key.trim().toLowerCase();
    const authResponse = mode === "signUp"
      ? await supabase.auth.signUp({
          email,
          password: loginData.password,
          options: {
            data: {
              full_name: loginData.user_name.trim(),
              address: loginData.user_address.trim(),
            },
          },
        })
      : await supabase.auth.signInWithPassword({
          email,
          password: loginData.password,
        });

    if (authResponse.error) {
      setError(authResponse.error.message);
      return;
    }

    const authUser = authResponse.data.user;
    if (!authUser) {
      setError("Please check your email to confirm the account, then sign in.");
      return;
    }
    if (mode === "signUp" && !authResponse.data.session) {
      setError("Account created. Please check your email to confirm it, then sign in.");
      return;
    }

    const profile = {
      user_key: authUser.id,
      email,
      user_name: loginData.user_name.trim() || authUser.user_metadata?.full_name || email,
      user_address: loginData.user_address.trim() || authUser.user_metadata?.address || "",
    };
    localStorage.setItem(SAVED_PROFILE_KEY, JSON.stringify(profile));
    setCurrentUser(profile);
    setLookupName(profile.user_key);
    setFormData((current) => ({
      ...current,
      user_name: profile.user_name,
      user_address: profile.user_address,
    }));
    setError("");
  };

  const handleLogout = async () => {
    if (supabase) {
      await supabase.auth.signOut();
    }
    localStorage.removeItem(SAVED_PROFILE_KEY);
    setCurrentUser(null);
    setLoginData({ user_key: "", password: "", confirm_password: "", user_name: "", user_address: "" });
    setLookupName("");
    setResult(null);
    setDashboard(null);
    setApplications([]);
    setFormData({ user_name: "", user_address: "", query: "", reference_number: "" });
    setActiveView("generate");
  };

  const updateStatus = async (applicationId, status) => {
    if (!activeLookup) return;
    try {
      await axios.patch(`${API_BASE}/my-rtis/${applicationId}/status`, {
        user_name: displayName,
        user_key: activeLookup,
        status,
      });
      await loadDashboard(activeLookup);
    } catch (err) {
      setError("Status update failed. Please try again.");
    }
  };

  const handleReset = () => {
    setResult(null);
    setCopied(false);
    setFormData({
      user_name: currentUser?.user_name || "",
      user_address: currentUser?.user_address || "",
      query: "",
      reference_number: "",
    });
  };

  const handleCopy = () => {
    if (!result?.draft) return;
    navigator.clipboard.writeText(result.draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!currentUser) {
    return (
      <LoginScreen
        loginData={loginData}
        setLoginData={setLoginData}
        authMode={authMode}
        setAuthMode={setAuthMode}
        onLogin={handleLogin}
        error={error}
      />
    );
  }

  return (
    <div style={styles.page}>
      <aside style={styles.sidebar}>
        <div style={styles.brandBlock}>
          <div style={styles.brandMark}>AI</div>
          <div>
            <div style={styles.brandTitle}>RTI Agentic AI</div>
            <div style={styles.brandSub}>Citizen service desk</div>
          </div>
        </div>

        <button style={navStyle(activeView === "generate")} onClick={() => setActiveView("generate")}>
          Generate RTI
        </button>
        <button style={navStyle(activeView === "dashboard")} onClick={() => setActiveView("dashboard")}>
          Dashboard
        </button>
        <button style={navStyle(activeView === "applications")} onClick={() => setActiveView("applications")}>
          My RTIs
        </button>

        <div style={styles.sidebarPanel}>
          <div style={styles.panelLabel}>How it works</div>
          <div style={styles.panelText}>Our AI reads your problem, finds the right government office, writes your RTI letter, and tracks the deadline — all in seconds.</div>
        </div>

          <div style={styles.profilePanel}>
            <div style={styles.panelLabel}>Signed in as</div>
            <div style={styles.profileName}>{currentUser.user_name}</div>
            <button style={styles.logoutButton} onClick={handleLogout}>Logout</button>
          </div>
      </aside>

      <main style={styles.main}>
        <header style={styles.topbar}>
          <div>
            <div style={styles.eyebrow}>Agentic AI-Based RTI Management System</div>
            <h1 style={styles.title}>Smart RTI Assistant Dashboard</h1>
          </div>
          <div style={styles.userLookup}>
            <input
             style={styles.lookupInput}
             value={currentUser.user_name}
             readOnly
           />
           <button style={styles.smallButton} onClick={handleLoadLookup}>
             Load
           </button>
         </div>
        </header>

        {error && <div style={styles.error}>{error}</div>}

        {activeView === "generate" && (
          <div style={styles.contentGrid}>
            <section style={styles.surface}>
              <div style={styles.sectionHeader}>
                <div>
                  <h2 style={styles.sectionTitle}>Citizen Intake</h2>
                  <p style={styles.sectionSub}>Describe your problem in simple words and we will prepare your RTI application automatically.</p>
                </div>
                <span style={styles.liveBadge}>Ready</span>
              </div>

              {!result ? (
                <>
                  <Field label="Full name" required>
                    <input
                      style={styles.input}
                      placeholder="e.g. Rahul Sharma"
                      value={formData.user_name}
                      readOnly
                    />
                  </Field>
                  <Field label="Address" required>
                    <input
                      style={styles.input}
                      placeholder="e.g. Andheri, Mumbai, Maharashtra"
                      value={formData.user_address}
                      readOnly
                    />
                  </Field>
                  <Field label="Reference number">
                    <input
                      style={styles.input}
                      placeholder="Optional application or reference number"
                      value={formData.reference_number}
                      onChange={(event) => updateForm("reference_number", event.target.value)}
                    />
                  </Field>
                  <Field label="Describe the issue" required>
                    <textarea
                      style={styles.textarea}
                      placeholder="e.g. My passport application has been pending for 8 months and I have received no update."
                      value={formData.query}
                      onChange={(event) => updateForm("query", event.target.value)}
                    />
                  </Field>
                  <button style={loading ? styles.primaryDisabled : styles.primaryButton} onClick={handleSubmit} disabled={loading}>
                    {loading ? "Preparing your RTI application..." : "Generate RTI Application"}
                  </button>
                </>
              ) : (
                <ResultPanel result={result} copied={copied} onCopy={handleCopy} onReset={handleReset} />
              )}
            </section>

            <section style={styles.surface}>
              <h2 style={styles.sectionTitle}>How your RTI is prepared</h2>
              <div style={styles.agentList}>
                {agentSteps.map(([name, detail], index) => (
                  <div key={name} style={styles.agentItem}>
                    <div style={result || index === 0 ? styles.agentDotDone : styles.agentDot}>{index + 1}</div>
                    <div>
                      <div style={styles.agentName}>{name}</div>
                      <div style={styles.agentDetail}>{detail}</div>
                    </div>
                  </div>
                ))}
              </div>

              {result && (
                <div style={styles.analysisBox}>
                  <div style={styles.panelLabel}>Latest agent output</div>
                  <div style={styles.analysisRow}><span>Department</span><strong>{result.authority.department}</strong></div>
                  <div style={styles.analysisRow}><span>State</span><strong>{result.intent.state}</strong></div>
                  <div style={styles.analysisRow}><span>Deadline</span><strong>{result.tracker.deadline_date}</strong></div>
                  <div style={styles.analysisRow}><span>Quality</span><strong>{result.review.passed ? "Passed" : "Needs review"}</strong></div>
                </div>
              )}
            </section>
          </div>
        )}

        {activeView === "dashboard" && (
          <DashboardView
            dashboard={dashboard}
            loading={dashboardLoading}
            userName={displayName}
            onLoad={() => loadDashboard(activeLookup)}
          />
        )}

        {activeView === "applications" && (
          <ApplicationsView
            applications={applications}
            loading={dashboardLoading}
            userName={displayName}
            onStatusChange={updateStatus}
            selectedApplication={selectedApplication}
            onViewApplication={setSelectedApplication}
            onLoad={() => loadDashboard(activeLookup)}
          />
        )}
      </main>
    </div>
  );
}

function Field({ label, required, children }) {
  return (
    <label style={styles.field}>
      <span style={styles.label}>{label}{required && <b style={styles.required}> *</b>}</span>
      {children}
    </label>
  );
}

function LoginScreen({ loginData, setLoginData, authMode, setAuthMode, onLogin, error }) {
  const isSignUp = authMode === "signUp";

  const switchMode = (mode) => {
    setAuthMode(mode);
    setLoginData({
      user_key: loginData.user_key,
      password: "",
      confirm_password: "",
      user_name: mode === "signUp" ? loginData.user_name : "",
      user_address: mode === "signUp" ? loginData.user_address : "",
    });
  };

  return (
    <div style={styles.loginPage}>
      <section style={styles.loginPanel}>
        <div style={styles.loginBrand}>
          <div style={styles.brandMark}>AI</div>
          <div>
            <div style={styles.brandTitle}>RTI Agentic AI</div>
            <div style={styles.brandSub}>Citizen service desk</div>
          </div>
        </div>

        <div style={styles.eyebrow}>Secure citizen workspace</div>
        <h1 style={styles.loginTitle}>{isSignUp ? "Create your RTI account" : "Sign in to track your RTI cases"}</h1>
        <div style={styles.authTabs}>
          <button style={authTabStyle(!isSignUp)} onClick={() => switchMode("signIn")}>Sign In</button>
          <button style={authTabStyle(isSignUp)} onClick={() => switchMode("signUp")}>Create Account</button>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <Field label="Email" required>
          <input
            style={styles.input}
            placeholder="e.g. pooja@email.com"
            value={loginData.user_key}
            onChange={(event) => setLoginData({ ...loginData, user_key: event.target.value })}
          />
        </Field>
        <Field label={isSignUp ? "Create password" : "Password"} required>
          <input
            style={styles.input}
            type="password"
            placeholder="Enter password"
            value={loginData.password}
            onChange={(event) => setLoginData({ ...loginData, password: event.target.value })}
          />
        </Field>
        {isSignUp && (
          <>
            <Field label="Confirm password" required>
              <input
                style={styles.input}
                type="password"
                placeholder="Re-enter password"
                value={loginData.confirm_password}
                onChange={(event) => setLoginData({ ...loginData, confirm_password: event.target.value })}
              />
            </Field>
            <Field label="Full name" required>
              <input
                style={styles.input}
                placeholder="e.g. Pooja Patil"
                value={loginData.user_name}
                onChange={(event) => setLoginData({ ...loginData, user_name: event.target.value })}
              />
            </Field>
            <Field label="Address" required>
              <input
                style={styles.input}
                placeholder="e.g. Pune, Maharashtra"
                value={loginData.user_address}
                onChange={(event) => setLoginData({ ...loginData, user_address: event.target.value })}
              />
            </Field>
          </>
        )}

        <button style={styles.primaryButton} onClick={() => onLogin(authMode)}>
          {isSignUp ? "Create Account" : "Sign In"}
        </button>

        <div style={styles.loginNote}>
          Auth is handled by Supabase. RTI records are linked to the logged-in user's unique auth ID.
        </div>
      </section>

      <section style={styles.loginShowcase}>
        <div style={styles.showcaseCard}>
          <div style={styles.panelLabel}>Agent workflow</div>
          <div style={styles.showcaseTitle}>Read -> Understand -> Find Office -> Write -> Check -> Save</div>
          <div style={styles.showcaseGrid}>
            <Metric label="Storage" value="Supabase-ready" />
            <Metric label="Agents" value="6" />
            <Metric label="Tracking" value="Live" />
            <Metric label="Mode" value="RTI" />
          </div>
        </div>
      </section>
    </div>
  );
}

function ResultPanel({ result, copied, onCopy, onReset }) {
  const handlePrintDraft = () => {
    const printWindow = window.open("", "_blank", "width=900,height=1100");
    if (!printWindow) return;

    printWindow.document.write(buildPrintableRtiHtml(result.draft));
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 300);
  };

  return (
    <div>
      <div style={styles.successBanner}>RTI application generated and saved to tracking dashboard.</div>
      <div style={styles.miniGrid}>
        <Metric label="Department" value={result.authority.department} />
        <Metric label="Category" value={result.authority.category || result.authority.department} />
        <Metric label="AI Confidence" value={result.authority.confidence || "90%"} />
        <Metric label="PIO" value={result.authority.pio_name} />
        <Metric label="Deadline" value={result.tracker.deadline_date} />
        <Metric label="Words" value={`${result.review.word_count}/${result.review.max_words}`} />
      </div>
      <div style={styles.statusTimeline}>
        {["Generated", "Submitted", "Under Review", "Reply Received", "Closed"].map((step, index) => (
          <div key={step} style={styles.statusStep}>
            <span style={index === 0 ? styles.statusDotActive : styles.statusDot}>{index + 1}</span>
            <span>{step}</span>
          </div>
        ))}
      </div>
      <div style={styles.letterHeader}>
        <h3 style={styles.resultTitle}>Generated RTI Application</h3>
        <button style={styles.copyButton} onClick={onCopy}>{copied ? "Copied" : "Copy"}</button>
      </div>
      <pre style={styles.letterBox}>{result.draft}</pre>
      <div style={styles.actionRow}>
        <button style={styles.primaryButton} onClick={handlePrintDraft}>Print or Save PDF</button>
        <button style={styles.secondaryButton} onClick={onReset}>File Another RTI</button>
      </div>
    </div>
  );
}

function buildPrintableRtiHtml(draft) {
  const safeDraft = escapeHtml(draft);
  return `<!doctype html>
<html>
  <head>
    <title>RTI Application</title>
    <style>
      @page { size: A4; margin: 18mm; }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        color: #111827;
        background: #ffffff;
        font-family: "Times New Roman", Times, serif;
        font-size: 12pt;
        line-height: 1.55;
      }
      .document {
        width: 100%;
      }
      .header {
        border-bottom: 1px solid #d1d5db;
        margin-bottom: 18px;
        padding-bottom: 10px;
      }
      .title {
        margin: 0;
        font-family: Arial, sans-serif;
        font-size: 14pt;
        font-weight: 700;
      }
      .subtitle {
        margin: 4px 0 0;
        color: #4b5563;
        font-family: Arial, sans-serif;
        font-size: 9pt;
      }
      pre {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: "Times New Roman", Times, serif;
        font-size: 12pt;
        line-height: 1.6;
      }
      .footer {
        margin-top: 22px;
        border-top: 1px solid #e5e7eb;
        padding-top: 8px;
        color: #6b7280;
        font-family: Arial, sans-serif;
        font-size: 8pt;
      }
      @media print {
        .no-print { display: none; }
      }
    </style>
  </head>
  <body>
    <main class="document">
      <div class="header">
        <h1 class="title">RTI Application</h1>
        <p class="subtitle">Generated by RTI Agentic AI Assistant</p>
      </div>
      <pre>${safeDraft}</pre>
      <div class="footer">Please verify all details before filing this RTI application.</div>
    </main>
  </body>
</html>`;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function DashboardView({ dashboard, loading, userName, onLoad }) {
  if (!userName) return <EmptyState title="Load a citizen profile" text="Enter a user name in the top-right box to view dashboard analytics." />;
  if (loading) return <EmptyState title="Loading dashboard" text="Fetching RTI metrics and recent cases." />;

  const topDepartments = dashboard?.top_departments || [];
  const maxCount = Math.max(...topDepartments.map((item) => item.count), 1);

  return (
    <div>
      <div style={styles.dashboardHeader}>
        <div>
          <h2 style={styles.sectionTitle}>Analytics Overview</h2>
          <p style={styles.sectionSub}>Live case summary for {userName}</p>
        </div>
        <button style={styles.smallButton} onClick={onLoad}>Refresh</button>
      </div>

      <div style={styles.statsGrid}>
        <Metric label="Total RTIs" value={dashboard?.total_applications || 0} />
        <Metric label="Pending Cases" value={dashboard?.pending_cases || 0} />
        <Metric label="Urgent Cases" value={dashboard?.urgent_cases || 0} />
        <Metric label="Closed Cases" value={dashboard?.closed_cases || 0} />
      </div>

      <div style={styles.contentGrid}>
        <section style={styles.surface}>
          <h2 style={styles.sectionTitle}>Department Analytics</h2>
          {topDepartments.length ? topDepartments.map((item) => (
            <div key={item.department} style={styles.barRow}>
              <div style={styles.barLabel}>{item.department}</div>
              <div style={styles.barTrack}>
                <div style={{ ...styles.barFill, width: `${(item.count / maxCount) * 100}%` }} />
              </div>
              <div style={styles.barCount}>{item.count}</div>
            </div>
          )) : <p style={styles.muted}>No RTIs filed yet.</p>}
        </section>

        <section style={styles.surface}>
          <h2 style={styles.sectionTitle}>Recent Agent Activity</h2>
          {(dashboard?.recent_applications || []).length ? dashboard.recent_applications.map((app) => (
            <div key={app.id} style={styles.timelineItem}>
              <span style={priorityStyle(app.priority)}>{app.priority}</span>
              <div>
                <div style={styles.agentName}>{app.department}</div>
                <div style={styles.agentDetail}>{app.status} | Deadline: {app.deadline_date}</div>
              </div>
            </div>
          )) : <p style={styles.muted}>Generate an RTI to see activity here.</p>}
        </section>
      </div>
    </div>
  );
}

function ApplicationsView({
  applications,
  loading,
  userName,
  onStatusChange,
  selectedApplication,
  onViewApplication,
  onLoad,
}) {
  if (!userName) return <EmptyState title="Load My RTIs" text="Enter the same user name used while filing RTIs." />;
  if (loading) return <EmptyState title="Loading applications" text="Fetching saved RTI cases." />;

  return (
    <section style={styles.surface}>
      <div style={styles.dashboardHeader}>
        <div>
          <h2 style={styles.sectionTitle}>My RTI Applications</h2>
          <p style={styles.sectionSub}>Track deadlines, priority, department, and current lifecycle status.</p>
        </div>
        <button style={styles.smallButton} onClick={onLoad}>Refresh</button>
      </div>

      <div style={styles.tableWrap}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>ID</th>
              <th style={styles.th}>Subject</th>
              <th style={styles.th}>Department</th>
              <th style={styles.th}>Priority</th>
              <th style={styles.th}>Deadline</th>
              <th style={styles.th}>Status</th>
              <th style={styles.th}>Letter</th>
            </tr>
          </thead>
          <tbody>
            {applications.length ? applications.map((app) => (
              <tr key={app.id}>
                <td style={styles.td}>#{app.id}</td>
                <td style={styles.td}>{app.subject}</td>
                <td style={styles.td}>{app.department}</td>
                <td style={styles.td}><span style={priorityStyle(app.priority)}>{app.priority}</span></td>
                <td style={styles.td}>{app.deadline_date}<br /><span style={styles.muted}>{app.days_remaining} days left</span></td>
                <td style={styles.td}>
                  <select style={styles.select} value={app.status} onChange={(event) => onStatusChange(app.id, event.target.value)}>
                    {STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}
                  </select>
                </td>
                <td style={styles.td}>
                  <button style={styles.tableButton} onClick={() => onViewApplication(app)}>
                    View Letter
                  </button>
                </td>
              </tr>
            )) : (
              <tr>
                <td style={styles.emptyCell} colSpan="7">No RTI applications found for this name.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {selectedApplication && <SavedApplicationPanel application={selectedApplication} />}
    </section>
  );
}

function SavedApplicationPanel({ application }) {
  const handlePrint = () => {
    const printWindow = window.open("", "_blank", "width=900,height=1100");
    if (!printWindow) return;
    printWindow.document.write(buildPrintableRtiHtml(application.draft));
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 300);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(application.draft || "");
  };

  return (
    <div style={styles.savedLetterPanel}>
      <div style={styles.letterHeader}>
        <div>
          <h3 style={styles.resultTitle}>Saved RTI Letter #{application.id}</h3>
          <p style={styles.sectionSub}>{application.department} | Deadline: {application.deadline_date}</p>
        </div>
        <div style={styles.actionRowCompact}>
          <button style={styles.copyButton} onClick={handleCopy}>Copy</button>
          <button style={styles.smallButton} onClick={handlePrint}>Print or Save PDF</button>
        </div>
      </div>
      <pre style={styles.letterBox}>{application.draft || "No saved draft found for this RTI."}</pre>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div style={styles.metricCard}>
      <div style={styles.metricLabel}>{label}</div>
      <div style={styles.metricValue}>{value}</div>
    </div>
  );
}

function EmptyState({ title, text }) {
  return (
    <section style={styles.surface}>
      <h2 style={styles.sectionTitle}>{title}</h2>
      <p style={styles.sectionSub}>{text}</p>
    </section>
  );
}

const navStyle = (active) => ({
  width: "100%",
  textAlign: "left",
  padding: "12px 14px",
  borderRadius: 8,
  border: "1px solid transparent",
  background: active ? "#20324a" : "transparent",
  color: active ? "#ffffff" : "#9fb0c7",
  fontSize: 14,
  fontWeight: 700,
  cursor: "pointer",
  marginBottom: 8,
});

const authTabStyle = (active) => ({
  flex: 1,
  padding: "10px 12px",
  borderRadius: 8,
  border: active ? "1px solid #38bdf8" : "1px solid #2b3b55",
  background: active ? "#20324a" : "#0f1720",
  color: active ? "#ffffff" : "#94a3b8",
  fontSize: 13,
  fontWeight: 900,
  cursor: "pointer",
});

const priorityStyle = (priority) => ({
  display: "inline-flex",
  padding: "4px 9px",
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 800,
  color: priority === "High" ? "#fecaca" : priority === "Medium" ? "#fde68a" : "#bbf7d0",
  background: priority === "High" ? "#7f1d1d" : priority === "Medium" ? "#78350f" : "#064e3b",
});

const styles = {
  loginPage: {
    minHeight: "100vh",
    background: "#0f1720",
    color: "#e5edf7",
    display: "grid",
    gridTemplateColumns: "minmax(360px, 0.8fr) minmax(420px, 1.2fr)",
    gap: 22,
    alignItems: "center",
    padding: 32,
    boxSizing: "border-box",
    fontFamily: "'Segoe UI', Arial, sans-serif",
  },
  loginPanel: {
    background: "#151f2e",
    border: "1px solid #24344d",
    borderRadius: 8,
    padding: 28,
    boxShadow: "0 14px 34px rgba(0,0,0,0.24)",
  },
  loginBrand: { display: "flex", alignItems: "center", gap: 12, marginBottom: 28 },
  loginTitle: { margin: "8px 0 10px", fontSize: 34, lineHeight: 1.1, color: "#ffffff" },
  loginText: { margin: "0 0 22px", color: "#b7c5d8", fontSize: 14, lineHeight: 1.6 },
  loginNote: {
    marginTop: 18,
    padding: 12,
    borderRadius: 8,
    background: "#0d2534",
    border: "1px solid #16445f",
    color: "#b7c5d8",
    fontSize: 12,
    lineHeight: 1.5,
  },
  authTabs: { display: "flex", gap: 8, marginBottom: 18 },
  loginShowcase: {
    minHeight: 520,
    borderRadius: 8,
    border: "1px solid #24344d",
    background: "linear-gradient(135deg, #122033, #08111d)",
    display: "flex",
    alignItems: "flex-end",
    padding: 24,
    boxSizing: "border-box",
  },
  showcaseCard: {
    width: "100%",
    background: "rgba(21,31,46,0.92)",
    border: "1px solid #2b3b55",
    borderRadius: 8,
    padding: 22,
  },
  showcaseTitle: { color: "#ffffff", fontSize: 24, fontWeight: 900, lineHeight: 1.25, marginBottom: 18 },
  showcaseGrid: { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 },
  page: {
    minHeight: "100vh",
    background: "#0f1720",
    color: "#e5edf7",
    display: "flex",
    fontFamily: "'Segoe UI', Arial, sans-serif",
  },
  sidebar: {
    width: 260,
    background: "#111b29",
    borderRight: "1px solid #223047",
    padding: 22,
    boxSizing: "border-box",
    position: "sticky",
    top: 0,
    height: "100vh",
  },
  brandBlock: { display: "flex", alignItems: "center", gap: 12, marginBottom: 28 },
  brandMark: {
    width: 42,
    height: 42,
    borderRadius: 8,
    display: "grid",
    placeItems: "center",
    background: "#38bdf8",
    color: "#082f49",
    fontWeight: 900,
  },
  brandTitle: { fontSize: 17, fontWeight: 800 },
  brandSub: { fontSize: 12, color: "#7d8da5", marginTop: 3 },
  sidebarPanel: {
    marginTop: 28,
    padding: 14,
    borderRadius: 8,
    background: "#0d2534",
    border: "1px solid #16445f",
  },
  profilePanel: {
    marginTop: 18,
    padding: 14,
    borderRadius: 8,
    background: "#151f2e",
    border: "1px solid #24344d",
  },
  profileName: { color: "#ffffff", fontSize: 15, fontWeight: 900, marginBottom: 4 },
  profileAddress: { color: "#94a3b8", fontSize: 12, lineHeight: 1.4, marginBottom: 12 },
  logoutButton: {
    width: "100%",
    background: "transparent",
    color: "#bae6fd",
    border: "1px solid #38bdf8",
    borderRadius: 8,
    padding: "9px 10px",
    fontSize: 12,
    fontWeight: 900,
    cursor: "pointer",
  },
  panelLabel: { fontSize: 12, textTransform: "uppercase", color: "#38bdf8", fontWeight: 900, marginBottom: 8 },
  panelText: { fontSize: 13, lineHeight: 1.5, color: "#b7c5d8" },
  main: { flex: 1, padding: 28, boxSizing: "border-box", overflow: "auto" },
  topbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 16,
    marginBottom: 24,
  },
  eyebrow: { color: "#38bdf8", fontSize: 12, fontWeight: 900, textTransform: "uppercase", letterSpacing: 0 },
  title: { margin: "5px 0 0", fontSize: 34, lineHeight: 1.1, color: "#ffffff" },
  userLookup: { display: "flex", gap: 8, alignItems: "center" },
  lookupInput: {
    width: 260,
    background: "#111b29",
    color: "#e5edf7",
    border: "1px solid #2b3b55",
    borderRadius: 8,
    padding: "11px 12px",
    fontSize: 14,
    outline: "none",
  },
  smallButton: {
    background: "#38bdf8",
    color: "#082f49",
    border: "none",
    borderRadius: 8,
    padding: "11px 14px",
    fontSize: 13,
    fontWeight: 900,
    cursor: "pointer",
  },
  contentGrid: { display: "grid", gridTemplateColumns: "minmax(0, 1.4fr) minmax(320px, 0.8fr)", gap: 18 },
  surface: {
    background: "#151f2e",
    border: "1px solid #24344d",
    borderRadius: 8,
    padding: 22,
    boxShadow: "0 14px 34px rgba(0,0,0,0.18)",
  },
  sectionHeader: { display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", marginBottom: 18 },
  dashboardHeader: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 18 },
  sectionTitle: { margin: 0, fontSize: 20, color: "#ffffff" },
  sectionSub: { margin: "6px 0 0", color: "#94a3b8", fontSize: 14, lineHeight: 1.5 },
  liveBadge: {
    color: "#bbf7d0",
    background: "#064e3b",
    padding: "5px 10px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 800,
  },
  field: { display: "block", marginBottom: 14 },
  label: { display: "block", color: "#cbd5e1", fontSize: 13, fontWeight: 800, marginBottom: 7 },
  required: { color: "#f87171" },
  input: {
    width: "100%",
    background: "#0f1720",
    color: "#e5edf7",
    border: "1px solid #2b3b55",
    borderRadius: 8,
    padding: "12px 13px",
    boxSizing: "border-box",
    fontSize: 14,
    outline: "none",
  },
  textarea: {
    width: "100%",
    minHeight: 130,
    background: "#0f1720",
    color: "#e5edf7",
    border: "1px solid #2b3b55",
    borderRadius: 8,
    padding: "12px 13px",
    boxSizing: "border-box",
    resize: "vertical",
    fontFamily: "inherit",
    fontSize: 14,
    outline: "none",
  },
  primaryButton: {
    background: "#38bdf8",
    color: "#082f49",
    border: "none",
    borderRadius: 8,
    padding: "13px 16px",
    fontSize: 14,
    fontWeight: 900,
    cursor: "pointer",
  },
  primaryDisabled: {
    background: "#64748b",
    color: "#e2e8f0",
    border: "none",
    borderRadius: 8,
    padding: "13px 16px",
    fontSize: 14,
    fontWeight: 800,
    cursor: "not-allowed",
  },
  secondaryButton: {
    background: "transparent",
    color: "#bae6fd",
    border: "1px solid #38bdf8",
    borderRadius: 8,
    padding: "13px 16px",
    fontSize: 14,
    fontWeight: 900,
    cursor: "pointer",
  },
  error: {
    background: "#451a1a",
    border: "1px solid #7f1d1d",
    color: "#fecaca",
    borderRadius: 8,
    padding: "12px 14px",
    marginBottom: 16,
    fontWeight: 700,
  },
  successBanner: {
    background: "#064e3b",
    color: "#bbf7d0",
    border: "1px solid #047857",
    borderRadius: 8,
    padding: 12,
    fontWeight: 800,
    marginBottom: 14,
  },
  agentList: { display: "grid", gap: 12, marginTop: 18 },
  agentItem: { display: "flex", gap: 12, alignItems: "center", padding: 12, borderRadius: 8, background: "#0f1720" },
  agentDot: {
    width: 30,
    height: 30,
    borderRadius: 999,
    display: "grid",
    placeItems: "center",
    background: "#1e293b",
    color: "#94a3b8",
    fontWeight: 900,
    fontSize: 12,
    flexShrink: 0,
  },
  agentDotDone: {
    width: 30,
    height: 30,
    borderRadius: 999,
    display: "grid",
    placeItems: "center",
    background: "#0ea5e9",
    color: "#082f49",
    fontWeight: 900,
    fontSize: 12,
    flexShrink: 0,
  },
  agentName: { color: "#e2e8f0", fontWeight: 850, fontSize: 14 },
  agentDetail: { color: "#94a3b8", fontSize: 12, marginTop: 3 },
  analysisBox: { marginTop: 18, padding: 14, borderRadius: 8, background: "#0f1720", border: "1px solid #263851" },
  analysisRow: { display: "flex", justifyContent: "space-between", gap: 12, color: "#94a3b8", fontSize: 13, padding: "8px 0", borderBottom: "1px solid #223047" },
  miniGrid: { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12, marginBottom: 18 },
  statsGrid: { display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 14, marginBottom: 18 },
  metricCard: { background: "#111b29", border: "1px solid #24344d", borderRadius: 8, padding: 16 },
  metricLabel: { color: "#94a3b8", fontSize: 12, fontWeight: 800, textTransform: "uppercase" },
  metricValue: { color: "#ffffff", fontSize: 24, fontWeight: 900, marginTop: 8, lineHeight: 1.1 },
  statusTimeline: {
    display: "grid",
    gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
    gap: 8,
    margin: "2px 0 20px",
  },
  statusStep: {
    minHeight: 54,
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "8px 10px",
    borderRadius: 8,
    background: "#0f1720",
    border: "1px solid #24344d",
    color: "#cbd5e1",
    fontSize: 12,
    fontWeight: 800,
  },
  statusDot: {
    width: 22,
    height: 22,
    borderRadius: 999,
    display: "grid",
    placeItems: "center",
    background: "#1e293b",
    color: "#94a3b8",
    fontSize: 11,
    fontWeight: 900,
    flexShrink: 0,
  },
  statusDotActive: {
    width: 22,
    height: 22,
    borderRadius: 999,
    display: "grid",
    placeItems: "center",
    background: "#38bdf8",
    color: "#082f49",
    fontSize: 11,
    fontWeight: 900,
    flexShrink: 0,
  },
  resultTitle: { margin: 0, fontSize: 17, color: "#ffffff" },
  letterHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 },
  copyButton: { background: "#20324a", color: "#dbeafe", border: "1px solid #385172", borderRadius: 8, padding: "8px 12px", fontWeight: 800, cursor: "pointer" },
  letterBox: {
    background: "#0f1720",
    border: "1px solid #263851",
    borderRadius: 8,
    color: "#dbeafe",
    padding: 16,
    whiteSpace: "pre-wrap",
    lineHeight: 1.65,
    fontSize: 13,
    maxHeight: 420,
    overflow: "auto",
  },
  actionRow: { display: "flex", gap: 10, marginTop: 14 },
  actionRowCompact: { display: "flex", gap: 10, alignItems: "center" },
  barRow: { display: "grid", gridTemplateColumns: "160px 1fr 34px", gap: 12, alignItems: "center", marginBottom: 14 },
  barLabel: { color: "#cbd5e1", fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  barTrack: { height: 10, background: "#0f1720", borderRadius: 999, overflow: "hidden" },
  barFill: { height: "100%", background: "#38bdf8", borderRadius: 999 },
  barCount: { color: "#ffffff", fontWeight: 900, fontSize: 13, textAlign: "right" },
  timelineItem: { display: "flex", alignItems: "center", gap: 12, padding: "12px 0", borderBottom: "1px solid #24344d" },
  savedLetterPanel: { marginTop: 22, paddingTop: 20, borderTop: "1px solid #2b3b55" },
  tableWrap: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse", minWidth: 820 },
  th: { textAlign: "left", color: "#94a3b8", fontSize: 12, textTransform: "uppercase", padding: "12px 10px", borderBottom: "1px solid #2b3b55" },
  td: { color: "#e2e8f0", fontSize: 13, padding: "13px 10px", borderBottom: "1px solid #24344d", verticalAlign: "top" },
  select: { background: "#0f1720", color: "#e2e8f0", border: "1px solid #2b3b55", borderRadius: 8, padding: "8px 9px", outline: "none" },
  tableButton: {
    background: "#20324a",
    color: "#dbeafe",
    border: "1px solid #385172",
    borderRadius: 8,
    padding: "8px 10px",
    fontSize: 12,
    fontWeight: 900,
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  muted: { color: "#94a3b8", fontSize: 12 },
  emptyCell: { textAlign: "center", color: "#94a3b8", padding: 30 },
};

export default App;
