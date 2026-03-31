import { type Agent } from "../api/mainlayer";

interface AgentCardProps {
  agent: Agent;
  onClick: (agent: Agent) => void;
  featured?: boolean;
}

export default function AgentCard({ agent, onClick, featured = false }: AgentCardProps) {
  const formattedPrice = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: agent.currency.toUpperCase(),
    minimumFractionDigits: 2,
  }).format(agent.price_per_call);

  return (
    <div
      onClick={() => onClick(agent)}
      style={{
        background: "var(--surface)",
        border: `1px solid ${featured ? "var(--brand)" : "var(--border)"}`,
        borderRadius: 12,
        padding: "1.25rem",
        cursor: "pointer",
        transition: "border-color 0.15s, transform 0.1s, box-shadow 0.15s",
        display: "flex",
        flexDirection: "column",
        gap: "0.75rem",
        position: "relative",
        overflow: "hidden",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = "var(--brand)";
        (e.currentTarget as HTMLDivElement).style.transform = "translateY(-2px)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "0 8px 24px rgba(99,102,241,0.15)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = featured ? "var(--brand)" : "var(--border)";
        (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "none";
      }}
    >
      {featured && (
        <span
          style={{
            position: "absolute",
            top: 12,
            right: 12,
            background: "var(--brand)",
            color: "#fff",
            fontSize: "0.65rem",
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            padding: "2px 8px",
            borderRadius: 99,
          }}
        >
          Featured
        </span>
      )}

      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: "var(--surface2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "1.4rem",
            flexShrink: 0,
          }}
        >
          {categoryEmoji(agent.category)}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3
            style={{
              fontSize: "0.95rem",
              fontWeight: 600,
              color: "var(--text)",
              marginBottom: 2,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {agent.name}
          </h3>
          <span
            style={{
              fontSize: "0.72rem",
              color: "var(--brand)",
              fontWeight: 500,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            {agent.category}
          </span>
        </div>
      </div>

      {/* Description */}
      <p
        style={{
          fontSize: "0.825rem",
          color: "var(--muted)",
          lineHeight: 1.55,
          display: "-webkit-box",
          WebkitLineClamp: 3,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
          flex: 1,
        }}
      >
        {agent.description}
      </p>

      {/* Tags */}
      {agent.tags.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {agent.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              style={{
                background: "var(--surface2)",
                color: "var(--muted)",
                borderRadius: 4,
                padding: "2px 7px",
                fontSize: "0.7rem",
                fontWeight: 500,
              }}
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          paddingTop: "0.5rem",
          borderTop: "1px solid var(--border)",
        }}
      >
        <div>
          <span style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text)" }}>
            {formattedPrice}
          </span>
          <span style={{ fontSize: "0.72rem", color: "var(--muted)", marginLeft: 4 }}>
            / call
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.75rem", color: "var(--muted)" }}>
          <span>{agent.call_count.toLocaleString()} calls</span>
          {agent.rating !== null && (
            <>
              <span>·</span>
              <span>★ {agent.rating.toFixed(1)}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function categoryEmoji(category: string): string {
  const map: Record<string, string> = {
    nlp: "💬",
    vision: "👁",
    code: "💻",
    data: "📊",
    finance: "💰",
    research: "🔬",
    creative: "🎨",
    automation: "⚙️",
    audio: "🎵",
    security: "🔒",
  };
  return map[category.toLowerCase()] ?? "🤖";
}
