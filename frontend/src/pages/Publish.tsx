import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { agentsApi, type Agent } from "../api/mainlayer";

const CATEGORIES = [
  "NLP", "Vision", "Code", "Data", "Finance",
  "Research", "Creative", "Automation", "Audio", "Security",
];

interface Capability {
  name: string;
  description: string;
}

export default function Publish() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    description: "",
    category: "NLP",
    price_per_call: "0.05",
    tags: "",
    example_input: "",
    example_output: "",
  });

  const [capabilities, setCapabilities] = useState<Capability[]>([
    { name: "", description: "" },
  ]);

  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<Agent | null>(null);
  const [error, setError] = useState<string | null>(null);

  const set = (key: string, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const setCapability = (index: number, field: keyof Capability, value: string) => {
    setCapabilities((prev) =>
      prev.map((cap, i) => (i === index ? { ...cap, [field]: value } : cap))
    );
  };

  const addCapability = () =>
    setCapabilities((prev) => [...prev, { name: "", description: "" }]);

  const removeCapability = (index: number) =>
    setCapabilities((prev) => prev.filter((_, i) => i !== index));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const price = parseFloat(form.price_per_call);
    if (isNaN(price) || price <= 0) {
      setError("Price per call must be a positive number.");
      return;
    }

    const validCapabilities = capabilities.filter(
      (c) => c.name.trim() && c.description.trim()
    );

    const tags = form.tags
      .split(",")
      .map((t) => t.trim().toLowerCase())
      .filter(Boolean);

    setSubmitting(true);
    try {
      const agent = await agentsApi.publish({
        name: form.name,
        description: form.description,
        category: form.category,
        price_per_call: price,
        capabilities: validCapabilities,
        tags,
        example_input: form.example_input || undefined,
        example_output: form.example_output || undefined,
      });
      setSuccess(agent);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to publish agent.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div style={{ maxWidth: 640, margin: "4rem auto", padding: "0 1.5rem", textAlign: "center" }}>
        <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🎉</div>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 800, marginBottom: "0.5rem" }}>
          Agent Published!
        </h2>
        <p style={{ color: "var(--muted)", marginBottom: "1.5rem" }}>
          <strong style={{ color: "var(--text)" }}>{success.name}</strong> is now live on the
          marketplace. Users can discover it and pay {" "}
          <strong style={{ color: "var(--brand)" }}>
            ${success.price_per_call.toFixed(2)}
          </strong>{" "}
          per call via Mainlayer.
        </p>
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 10,
            padding: "1rem 1.25rem",
            marginBottom: "1.5rem",
            fontFamily: "monospace",
            fontSize: "0.8rem",
            color: "var(--muted)",
            textAlign: "left",
          }}
        >
          <div style={{ marginBottom: 4 }}>
            <span style={{ color: "var(--brand)" }}>Agent ID:</span> {success.id}
          </div>
          <div>
            <span style={{ color: "var(--brand)" }}>Resource ID:</span> {success.resource_id}
          </div>
        </div>
        <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}>
          <button
            onClick={() => navigate(`/agents/${success.id}`)}
            style={primaryBtn}
          >
            View Agent Page
          </button>
          <button
            onClick={() => navigate("/")}
            style={secondaryBtn}
          >
            Back to Marketplace
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <button
        onClick={() => navigate(-1)}
        style={{ ...backBtn, marginBottom: "1.5rem" }}
      >
        ← Back
      </button>

      <h1 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "0.5rem" }}>
        Publish an Agent
      </h1>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: "2rem" }}>
        Register your AI agent as a billable resource. Mainlayer handles payments
        automatically — every call charges the user and pays you out.
      </p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        {/* Basic info */}
        <FormSection title="Basic Information">
          <Field label="Agent Name" required>
            <input
              type="text"
              placeholder="e.g. Smart Email Summarizer"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              required
              minLength={3}
              maxLength={80}
              style={fieldStyle}
            />
          </Field>

          <Field label="Description" required>
            <textarea
              placeholder="What does your agent do? Be specific about its capabilities and best use cases."
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              required
              minLength={10}
              maxLength={1000}
              rows={4}
              style={{ ...fieldStyle, resize: "vertical" }}
            />
          </Field>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <Field label="Category" required>
              <select
                value={form.category}
                onChange={(e) => set("category", e.target.value)}
                style={fieldStyle}
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </Field>

            <Field label="Price per Call (USD)" required>
              <div style={{ position: "relative" }}>
                <span
                  style={{
                    position: "absolute",
                    left: 12,
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "var(--muted)",
                    pointerEvents: "none",
                  }}
                >
                  $
                </span>
                <input
                  type="number"
                  min="0.001"
                  step="0.001"
                  placeholder="0.05"
                  value={form.price_per_call}
                  onChange={(e) => set("price_per_call", e.target.value)}
                  required
                  style={{ ...fieldStyle, paddingLeft: "1.75rem" }}
                />
              </div>
            </Field>
          </div>

          <Field label="Tags (comma-separated)">
            <input
              type="text"
              placeholder="e.g. summarization, email, productivity"
              value={form.tags}
              onChange={(e) => set("tags", e.target.value)}
              style={fieldStyle}
            />
          </Field>
        </FormSection>

        {/* Capabilities */}
        <FormSection title="Capabilities">
          {capabilities.map((cap, i) => (
            <div
              key={i}
              style={{
                background: "var(--surface2)",
                border: "1px solid var(--border)",
                borderRadius: 10,
                padding: "1rem",
                display: "flex",
                gap: "0.75rem",
                alignItems: "flex-start",
              }}
            >
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <input
                  type="text"
                  placeholder="Capability name"
                  value={cap.name}
                  onChange={(e) => setCapability(i, "name", e.target.value)}
                  style={{ ...fieldStyle, fontSize: "0.8rem" }}
                />
                <input
                  type="text"
                  placeholder="Short description"
                  value={cap.description}
                  onChange={(e) => setCapability(i, "description", e.target.value)}
                  style={{ ...fieldStyle, fontSize: "0.8rem" }}
                />
              </div>
              {capabilities.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeCapability(i)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--muted)",
                    cursor: "pointer",
                    fontSize: "1.1rem",
                    lineHeight: 1,
                    padding: "0.25rem",
                  }}
                >
                  ×
                </button>
              )}
            </div>
          ))}
          <button type="button" onClick={addCapability} style={ghostBtn}>
            + Add Capability
          </button>
        </FormSection>

        {/* Examples */}
        <FormSection title="Examples (optional)">
          <Field label="Example Input">
            <textarea
              placeholder='{"prompt": "Summarize this email..."}'
              value={form.example_input}
              onChange={(e) => set("example_input", e.target.value)}
              rows={3}
              style={{ ...fieldStyle, fontFamily: "monospace", fontSize: "0.8rem", resize: "vertical" }}
            />
          </Field>
          <Field label="Example Output">
            <textarea
              placeholder="The email discusses..."
              value={form.example_output}
              onChange={(e) => set("example_output", e.target.value)}
              rows={3}
              style={{ ...fieldStyle, fontFamily: "monospace", fontSize: "0.8rem", resize: "vertical" }}
            />
          </Field>
        </FormSection>

        {error && (
          <div
            style={{
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.3)",
              borderRadius: 8,
              padding: "0.75rem 1rem",
              color: "var(--danger)",
              fontSize: "0.875rem",
            }}
          >
            {error}
          </div>
        )}

        <button type="submit" disabled={submitting} style={{ ...primaryBtn, padding: "0.85rem", fontSize: "1rem" }}>
          {submitting ? "Publishing..." : "Publish Agent"}
        </button>
      </form>
    </div>
  );
}

function FormSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 14,
        padding: "1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      <h3 style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text)", marginBottom: "0.25rem" }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

function Field({
  label,
  required = false,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
      <label
        style={{
          fontSize: "0.75rem",
          fontWeight: 600,
          color: "var(--muted)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
        }}
      >
        {label}
        {required && <span style={{ color: "var(--danger)", marginLeft: 2 }}>*</span>}
      </label>
      {children}
    </div>
  );
}

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

const primaryBtn: React.CSSProperties = {
  background: "var(--brand)",
  color: "#fff",
  border: "none",
  borderRadius: 10,
  fontWeight: 700,
  cursor: "pointer",
  padding: "0.6rem 1.4rem",
  fontSize: "0.875rem",
};

const secondaryBtn: React.CSSProperties = {
  background: "var(--surface)",
  color: "var(--text)",
  border: "1px solid var(--border)",
  borderRadius: 10,
  fontWeight: 600,
  cursor: "pointer",
  padding: "0.6rem 1.4rem",
  fontSize: "0.875rem",
};

const ghostBtn: React.CSSProperties = {
  background: "transparent",
  border: "1px dashed var(--border)",
  borderRadius: 8,
  color: "var(--muted)",
  cursor: "pointer",
  padding: "0.5rem 1rem",
  fontSize: "0.825rem",
  fontWeight: 500,
  width: "100%",
};

const backBtn: React.CSSProperties = {
  background: "transparent",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--muted)",
  cursor: "pointer",
  padding: "0.4rem 0.9rem",
  fontSize: "0.85rem",
  display: "inline-block",
};
