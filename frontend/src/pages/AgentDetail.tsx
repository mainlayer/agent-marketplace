import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { agentsApi, paymentsApi, type Agent, type RunAgentResponse } from "../api/mainlayer";

export default function AgentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Run-agent form state
  const [apiKey, setApiKey] = useState("");
  const [inputJson, setInputJson] = useState('{\n  "prompt": "Hello, agent!"\n}');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RunAgentResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    agentsApi
      .get(id)
      .then(setAgent)
      .catch(() => setError("Agent not found."))
      .finally(() => setLoading(false));
  }, [id]);

  const handleRun = async () => {
    if (!agent || !apiKey.trim()) {
      setRunError("Please enter your Mainlayer API key.");
      return;
    }

    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(inputJson);
    } catch {
      setRunError("Input data must be valid JSON.");
      return;
    }

    setRunning(true);
    setRunError(null);
    setResult(null);

    try {
      const res = await paymentsApi.runAgent(agent.id, {
        payer_api_key: apiKey,
        input_data: parsed,
      });
      setResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Payment or agent execution failed.";
      setRunError(msg);
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <div style={{ maxWidth: 800, margin: "4rem auto", padding: "0 1.5rem", textAlign: "center" }}>
        <p style={{ color: "var(--muted)" }}>Loading agent...</p>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div style={{ maxWidth: 800, margin: "4rem auto", padding: "0 1.5rem", textAlign: "center" }}>
        <p style={{ color: "var(--danger)", marginBottom: "1rem" }}>{error ?? "Agent not found."}</p>
        <button onClick={() => navigate("/")} style={backBtn}>Back to Marketplace</button>
      </div>
    );
  }

  const formattedPrice = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: agent.currency.toUpperCase(),
    minimumFractionDigits: 2,
  }).format(agent.price_per_call);

  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Back */}
      <button
        onClick={() => navigate(-1)}
        style={{ ...backBtn, marginBottom: "1.5rem" }}
      >
        ← Back
      </button>

      {/* Header card */}
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 16,
          padding: "2rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", gap: "1.25rem", alignItems: "flex-start" }}>
          <div
            style={{
              width: 64,
              height: 64,
              background: "var(--surface2)",
              borderRadius: 14,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "2rem",
              flexShrink: 0,
            }}
          >
            🤖
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
              <h1 style={{ fontSize: "1.5rem", fontWeight: 800 }}>{agent.name}</h1>
              <span
                style={{
                  background: "var(--surface2)",
                  color: "var(--brand)",
                  borderRadius: 6,
                  padding: "2px 10px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                }}
              >
                {agent.category}
              </span>
            </div>
            <p style={{ color: "var(--muted)", marginTop: "0.5rem", lineHeight: 1.6, fontSize: "0.9rem" }}>
              {agent.description}
            </p>
            {agent.tags.length > 0 && (
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: "0.75rem" }}>
                {agent.tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      background: "var(--surface2)",
                      color: "var(--muted)",
                      borderRadius: 4,
                      padding: "2px 8px",
                      fontSize: "0.72rem",
                    }}
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Stats row */}
        <div
          style={{
            display: "flex",
            gap: "2rem",
            marginTop: "1.5rem",
            paddingTop: "1.25rem",
            borderTop: "1px solid var(--border)",
            flexWrap: "wrap",
          }}
        >
          <Stat label="Price per call" value={formattedPrice} highlight />
          <Stat label="Total calls" value={agent.call_count.toLocaleString()} />
          {agent.rating !== null && <Stat label="Rating" value={`★ ${agent.rating.toFixed(1)}`} />}
          <Stat label="Resource ID" value={agent.resource_id.slice(0, 16) + "..."} mono />
        </div>
      </div>

      {/* Capabilities */}
      {agent.capabilities.length > 0 && (
        <Section title="Capabilities">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "0.75rem" }}>
            {agent.capabilities.map((cap, i) => (
              <div
                key={i}
                style={{
                  background: "var(--surface2)",
                  borderRadius: 8,
                  padding: "0.85rem 1rem",
                  border: "1px solid var(--border)",
                }}
              >
                <div style={{ fontWeight: 600, fontSize: "0.875rem", marginBottom: 4 }}>{cap.name}</div>
                <div style={{ color: "var(--muted)", fontSize: "0.8rem" }}>{cap.description}</div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Examples */}
      {(agent.example_input || agent.example_output) && (
        <Section title="Examples">
          {agent.example_input && (
            <div style={{ marginBottom: "0.75rem" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: 4, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Input
              </div>
              <pre style={codeStyle}>{agent.example_input}</pre>
            </div>
          )}
          {agent.example_output && (
            <div>
              <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: 4, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Output
              </div>
              <pre style={codeStyle}>{agent.example_output}</pre>
            </div>
          )}
        </Section>
      )}

      {/* Pay & Run panel */}
      <Section title="Pay &amp; Run">
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: "1.5rem",
          }}
        >
          <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "1.25rem", lineHeight: 1.5 }}>
            Enter your Mainlayer API key and input data. Mainlayer will charge{" "}
            <strong style={{ color: "var(--text)" }}>{formattedPrice}</strong> from your balance
            and execute the agent immediately.
          </p>

          <label style={labelStyle}>Your Mainlayer API Key</label>
          <input
            type="password"
            placeholder="ml_live_..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            style={{ ...fieldStyle, marginBottom: "1rem", fontFamily: "monospace" }}
          />

          <label style={labelStyle}>Input Data (JSON)</label>
          <textarea
            value={inputJson}
            onChange={(e) => setInputJson(e.target.value)}
            rows={6}
            style={{ ...fieldStyle, marginBottom: "1.25rem", fontFamily: "monospace", resize: "vertical" }}
          />

          {runError && (
            <div
              style={{
                background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.3)",
                borderRadius: 8,
                padding: "0.75rem 1rem",
                marginBottom: "1rem",
                color: "var(--danger)",
                fontSize: "0.85rem",
              }}
            >
              {runError}
            </div>
          )}

          <button
            onClick={handleRun}
            disabled={running}
            style={{
              width: "100%",
              padding: "0.8rem",
              background: running ? "var(--surface2)" : "var(--brand)",
              color: "#fff",
              border: "none",
              borderRadius: 10,
              fontWeight: 700,
              fontSize: "0.95rem",
              cursor: running ? "not-allowed" : "pointer",
              transition: "background 0.15s",
            }}
          >
            {running ? "Processing payment..." : `Pay ${formattedPrice} & Run Agent`}
          </button>
        </div>

        {/* Result */}
        {result && (
          <div
            style={{
              marginTop: "1.25rem",
              background: "rgba(34,197,94,0.06)",
              border: "1px solid rgba(34,197,94,0.25)",
              borderRadius: 12,
              padding: "1.25rem 1.5rem",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                marginBottom: "0.75rem",
                color: "var(--success)",
                fontWeight: 600,
                fontSize: "0.875rem",
              }}
            >
              <span>Payment successful</span>
              <span style={{ color: "var(--muted)", fontWeight: 400 }}>
                · Payment ID: {result.payment_id}
              </span>
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--muted)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>
              Agent Output
            </div>
            <pre style={{ ...codeStyle, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {JSON.stringify(result.output, null, 2)}
            </pre>
          </div>
        )}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <h2
        style={{
          fontSize: "1rem",
          fontWeight: 700,
          marginBottom: "0.875rem",
          color: "var(--text)",
          paddingBottom: "0.5rem",
          borderBottom: "1px solid var(--border)",
        }}
        dangerouslySetInnerHTML={{ __html: title }}
      />
      {children}
    </div>
  );
}

function Stat({
  label,
  value,
  highlight = false,
  mono = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  mono?: boolean;
}) {
  return (
    <div>
      <div style={{ fontSize: "0.7rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 2 }}>
        {label}
      </div>
      <div
        style={{
          fontSize: "1rem",
          fontWeight: 700,
          color: highlight ? "var(--brand)" : "var(--text)",
          fontFamily: mono ? "monospace" : undefined,
        }}
      >
        {value}
      </div>
    </div>
  );
}

const backBtn: React.CSSProperties = {
  background: "transparent",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--muted)",
  cursor: "pointer",
  padding: "0.4rem 0.9rem",
  fontSize: "0.85rem",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.78rem",
  fontWeight: 600,
  color: "var(--muted)",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  marginBottom: "0.35rem",
};

const fieldStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.65rem 0.9rem",
  background: "var(--surface2)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--text)",
  fontSize: "0.875rem",
  outline: "none",
};

const codeStyle: React.CSSProperties = {
  background: "var(--surface2)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  padding: "1rem",
  fontSize: "0.8rem",
  color: "var(--text)",
  overflow: "auto",
  lineHeight: 1.6,
};
