import React, { useEffect, useMemo, useState } from "react";
import type { Claim, SignInResponse } from "./types";
import { apiGet, apiPost } from "./api";

// ---------- Small hooks ----------
function useClaims(status: "true" | "false") {
  const [items, setItems] = useState<Claim[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        setError("");
        // expects your backend to support: GET /claims?status=true|false
        const data = await apiGet<Claim[] | { items: Claim[] }>(`/claims?status=${status}`);
        const list = Array.isArray(data) ? data : (data.items ?? []);
        if (mounted) setItems(list);
      } catch (e: any) {
        if (mounted) setError(e.message || String(e));
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [status]);

  return { items, loading, error };
}

// ---------- UI sections ----------
function Landing({ onGoSignIn }:{ onGoSignIn: () => void }) {
  const trues = useClaims("true");
  const falses = useClaims("false");

  return (
    <div className="container main-container">
      {/* Hero */}
      <section className="card card-hero">
        <div className="hero-grid">
          <div>
            <h1 className="hero-title">Fact&nbsp;Shield</h1>
            <p className="hero-subtitle">
              A distributed fact-checking orchestration platform that <strong>connects platforms, government datasets, and independent fact-checkers</strong> to verify viral claims at scale.
            </p>
            <div className="hero-points">
              <div className="point">
                <span className="point-dot" />
                <div>
                  <div className="point-title">Neutral, Interoperable API</div>
                  <div className="point-text">Platforms (Meta, X, TikTok) submit claims via a standardized endpoint and receive transparent, source-cited decisions.</div>
                </div>
              </div>
              <div className="point">
                <span className="point-dot" />
                <div>
                  <div className="point-title">AI + Human in the Loop</div>
                  <div className="point-text">LLM + knowledge graph do first-pass verification with government/NGO data. Ambiguous cases escalate to certified fact-checkers.</div>
                </div>
              </div>
              <div className="point">
                <span className="point-dot" />
                <div>
                  <div className="point-title">Transparent & Privacy-Preserving</div>
                  <div className="point-text">Every decision cites sources; personal data is never processed—only public claims and datasets.</div>
                </div>
              </div>
            </div>
            <div className="hero-cta">
              <button className="btn btn-primary" onClick={onGoSignIn}>Sign in as Fact-Checker</button>
              <a className="btn btn-ghost" href="#" onClick={(e)=>e.preventDefault()}>API Docs (coming soon)</a>
            </div>
          </div>

          <div className="hero-card">
            <div className="hero-mini-title">How it works</div>
            <ol className="howitworks">
              <li><strong>Submit:</strong> Platforms send a claim to <code>/verify-claim</code>.</li>
              <li><strong>Triage:</strong> LLM + RAG match against government datasets.</li>
              <li><strong>Decide:</strong> Clear matches return <em>True/False</em> with citations.</li>
              <li><strong>Escalate:</strong> Unclear claims go to the fact-checker pool.</li>
              <li><strong>Consensus:</strong> Weighted votes finalize the outcome and update the knowledge base.</li>
            </ol>
          </div>
        </div>
      </section>

      {/* Live Panels */}
      <section className="cards-2col">
        <ClaimsPanel title="Verified True" color="#10b981" state={trues} />
        <ClaimsPanel title="Verified False" color="#ef4444" state={falses} />
      </section>

      {/* Trust & Governance */}
      <section className="card" style={{ marginTop: "20px" }}>
        <h3 className="section-title">Trust, Governance & Ethics</h3>
        <div className="two-col">
          <div>
            <div className="blurb-title">Datasets</div>
            <p className="blurb-text">
              Designed to ingest government and international data (e.g., Stats NZ, WHO, UN) for first-level automated validation with <strong>source links</strong> in responses.
            </p>
          </div>
          <div>
            <div className="blurb-title">Reputation-Weighted Voting</div>
            <p className="blurb-text">
              Fact-checker decisions are weighted by track record and bias-safety checks, preventing single-reviewer dominance.
            </p>
          </div>
          <div>
            <div className="blurb-title">Privacy by Design</div>
            <p className="blurb-text">
              No personal data processed. The system evaluates <em>claims</em> against <em>public</em> sources only.
            </p>
          </div>
          <div>
            <div className="blurb-title">Auditability</div>
            <p className="blurb-text">
              Every verdict includes a rationale and dataset references for downstream transparency and appeals.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function ClaimsPanel({ title, color, state }:{
  title: string; color: string;
  state: { items: Claim[]; loading: boolean; error: string };
}) {
  const { items, loading, error } = state;
  return (
    <div className="card">
      <div className="panel-head">
        <span className="status-dot" style={{ background: color }} />
        <h3 className="panel-title">{title}</h3>
      </div>
      {loading && <div className="muted">Loading…</div>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && items.length === 0 && (
        <div className="soft">Nothing here yet.</div>
      )}
      <ul className="claim-list">
        {items.map(c => (
          <li key={c.id} className="card card-inset">
            <div>{c.claim ?? c.claim_text}</div>
            <div className="claim-meta">
              Status: <span className="mono">{c.status}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SignIn({ onAuthed }:{
  onAuthed: (token: string, user: { id:string; email:string; name:string; org:string; role:string }) => void;
}) {
  const [email, setEmail] = useState("alice@example.org");
  const [password, setPassword] = useState("alice-pass");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      setLoading(true);
      setError("");
      const resp = await apiPost<SignInResponse>("/auth/signin", { email, password });
      onAuthed(resp.access_token, resp.user);
    } catch (err: any) {
      setError("Sign-in failed. Check credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container main-container center">
      <form onSubmit={submit} className="card auth-card">
        <h2 className="card-title">Fact Checker Sign In</h2>
        <label className="label">Email</label>
        <input className="input" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.org"/>
        <div style={{ height: 10 }} />
        <label className="label">Password</label>
        <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••"/>
        {error && <div className="error small">{error}</div>}
        <div style={{ height: 14 }} />
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Signing in…" : "Sign In"}
        </button>
      </form>
    </div>
  );
}

function FactCheckerDashboard({ token, user }:{
  token: string,
  user: { id:string; email:string; name:string; org:string; role:string } | null
}) {
  const [items, setItems] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    try {
      setLoading(true); setError("");
      const data = await apiGet<{ items: Claim[] }>(`/fact-checkers/${user?.id}/escalated`, token);
      setItems(data.items || []);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  async function castVote(id: string, vote: "true" | "false") {
    try {
      await apiPost(`/claims/${id}/vote`, { user_id: user?.id, vote }, token);
      setItems(xs => xs.filter(x => x.id !== id)); // remove after vote
    } catch (e: any) {
      alert("Vote failed: " + (e.message || String(e)));
    }
  }

  return (
    <div className="container main-container">
      <div className="dash-head">
        <h2 className="dash-title">Escalated Queue</h2>
        <button className="btn" style={{marginBottom: '10px'}} onClick={load}>Refresh</button>
      </div>
      {loading && <div className="muted">Loading…</div>}
      {error && <div className="error">{error}</div>}
      <ul className="claim-list">
        {items.map(c => (
          <li key={c.id} className="card card-inset">
            <div className="claim-text">{c.claim ?? c.claim_text}</div>
            {c.explanation && <div className="muted small">Reason: {c.explanation}</div>}
            <div className="vote-row">
              <button className="btn btn-primary" onClick={() => castVote(c.id, "true")}>Vote TRUE</button>
              <button className="btn btn-danger" onClick={() => castVote(c.id, "false")}>Vote FALSE</button>
            </div>
          </li>
        ))}
      </ul>
      {!loading && items.length === 0 && <div className="soft" style={{marginTop: '15px'}}>No pending items. 🎉</div>}
    </div>
  );
}

// ---------- Root ----------
export default function App() {
  const [route, setRoute] = useState<"landing" | "signin" | "dashboard">("landing");
  const [token, setToken] = useState<string>("");
  const [user, setUser] = useState<{ id:string; email:string; name:string; org:string; role:string } | null>(null);

  function onAuthed(tok: string, usr: any) {
    setToken(tok); setUser(usr); setRoute("dashboard");
  }
  function onSignOut() {
    setToken(""); setUser(null); setRoute("landing");
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="container header-inner">
          <div className="badge">
            <span className="badge-dot"></span>
            <strong>Fact Shield</strong>
          </div>
          <nav className="nav">
            <button onClick={() => setRoute("landing")} className={route==="landing"?"active":""}>Home</button>
            <button onClick={() => setRoute("signin")} className={route==="signin"?"active":""}>Sign In</button>
            <button onClick={() => setRoute("dashboard")} className={route==="dashboard"?"active":""}>Fact Checker</button>
          </nav>
          <div className="userbox">
            {user ? (
              <div className="userline">
                <span className="muted small">{user.name} • {user.org}</span>
                <button className="btn" onClick={onSignOut}>Sign out</button>
              </div>
            ) : (
              <span className="muted small">not signed in</span>
            )}
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="main">
        {route === "landing" && <Landing onGoSignIn={() => setRoute("signin")} />}
        {route === "signin" && <SignIn onAuthed={onAuthed} />}
        {route === "dashboard" && (token ? (
          <FactCheckerDashboard token={token} user={user} />
        ) : (
          <div className="container main-container">
            <div className="soft">Please sign in to access the fact-checker dashboard.</div>
          </div>
        ))}
      </main>

      {/* Footer (sticks to bottom) */}
      <footer className="footer">
        <div className="container footer-inner">
          © {new Date().getFullYear()} Fact Shield. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
