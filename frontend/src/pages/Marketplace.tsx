import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import AgentCard from "../components/AgentCard";
import { marketplaceApi, type Agent, type MarketplaceStats } from "../api/mainlayer";

const CATEGORIES = [
  "All", "NLP", "Vision", "Code", "Data", "Finance",
  "Research", "Creative", "Automation", "Audio", "Security",
];

const SORT_OPTIONS = [
  { label: "Newest", value: "created_at" },
  { label: "Most Used", value: "call_count" },
  { label: "Price: Low to High", value: "price_asc" },
  { label: "Price: High to Low", value: "price_desc" },
];

export default function Marketplace() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [stats, setStats] = useState<MarketplaceStats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [sort, setSort] = useState("created_at");
  const [page, setPage] = useState(0);
  const limit = 12;

  const [featuredIds, setFeaturedIds] = useState<Set<string>>(new Set());

  const fetchAgents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const sortBy = sort === "price_asc" || sort === "price_desc" ? "price_per_call" : sort;
      const sortOrder = sort === "price_asc" ? "asc" : "desc";

      const res = await marketplaceApi.discover({
        query: search || undefined,
        category: category !== "All" ? category : undefined,
        sort_by: sortBy as "created_at" | "price_per_call" | "call_count",
        sort_order: sortOrder,
        limit,
        offset: page * limit,
      });
      setAgents(res.agents);
      setTotal(res.total);
    } catch (err) {
      setError("Failed to load agents. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, [search, category, sort, page]);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  useEffect(() => {
    marketplaceApi.stats().then((s) => {
      setStats(s);
      setFeaturedIds(new Set(s.featured_agent_ids));
    }).catch(() => {});
  }, []);

  const totalPages = Math.ceil(total / limit);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Hero */}
      <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
        <h1 style={{ fontSize: "2.25rem", fontWeight: 800, marginBottom: "0.5rem" }}>
          Agent Marketplace
        </h1>
        <p style={{ color: "var(--muted)", fontSize: "1rem", maxWidth: 560, margin: "0 auto" }}>
          Discover and run AI agents. Every call is billed automatically through
          Mainlayer — no subscriptions, no minimums.
        </p>

        {stats && (
          <div
            style={{
              display: "flex",
              gap: "2rem",
              justifyContent: "center",
              marginTop: "1.5rem",
              flexWrap: "wrap",
            }}
          >
            {[
              { label: "Agents", value: stats.total_agents },
              { label: "Total Calls", value: stats.total_calls },
              { label: "Categories", value: stats.categories.length },
            ].map(({ label, value }) => (
              <div key={label} style={{ textAlign: "center" }}>
                <div style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--brand)" }}>
                  {value.toLocaleString()}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  {label}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Controls */}
      <div
        style={{
          display: "flex",
          gap: "0.75rem",
          marginBottom: "1.5rem",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <input
          type="text"
          placeholder="Search agents..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          style={inputStyle}
        />
        <select
          value={sort}
          onChange={(e) => { setSort(e.target.value); setPage(0); }}
          style={selectStyle}
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Category pills */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "2rem", flexWrap: "wrap" }}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => { setCategory(cat); setPage(0); }}
            style={{
              padding: "0.35rem 0.9rem",
              borderRadius: 99,
              border: "1px solid",
              borderColor: category === cat ? "var(--brand)" : "var(--border)",
              background: category === cat ? "var(--brand)" : "transparent",
              color: category === cat ? "#fff" : "var(--muted)",
              cursor: "pointer",
              fontSize: "0.8rem",
              fontWeight: 500,
              transition: "all 0.15s",
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Grid */}
      {loading ? (
        <LoadingGrid />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchAgents} />
      ) : agents.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: "1.25rem",
            }}
          >
            {agents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                featured={featuredIds.has(agent.id)}
                onClick={(a) => navigate(`/agents/${a.id}`)}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: "0.75rem",
                marginTop: "2.5rem",
              }}
            >
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                style={paginationBtn(page === 0)}
              >
                Previous
              </button>
              <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                Page {page + 1} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                style={paginationBtn(page >= totalPages - 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function LoadingGrid() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1.25rem" }}>
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          style={{
            height: 240,
            background: "var(--surface)",
            borderRadius: 12,
            border: "1px solid var(--border)",
            animation: "pulse 1.5s infinite",
          }}
        />
      ))}
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }`}</style>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div style={{ textAlign: "center", padding: "4rem 0" }}>
      <div style={{ fontSize: "2rem", marginBottom: "0.75rem" }}>⚠️</div>
      <p style={{ color: "var(--muted)", marginBottom: "1rem" }}>{message}</p>
      <button onClick={onRetry} style={primaryBtn}>Retry</button>
    </div>
  );
}

function EmptyState() {
  return (
    <div style={{ textAlign: "center", padding: "4rem 0" }}>
      <div style={{ fontSize: "2.5rem", marginBottom: "0.75rem" }}>🤖</div>
      <p style={{ color: "var(--muted)" }}>No agents found. Try a different search or category.</p>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  flex: 1,
  minWidth: 200,
  padding: "0.55rem 1rem",
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--text)",
  fontSize: "0.875rem",
  outline: "none",
};

const selectStyle: React.CSSProperties = {
  padding: "0.55rem 0.9rem",
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--text)",
  fontSize: "0.875rem",
  cursor: "pointer",
};

const primaryBtn: React.CSSProperties = {
  padding: "0.6rem 1.4rem",
  background: "var(--brand)",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  fontWeight: 600,
  cursor: "pointer",
  fontSize: "0.875rem",
};

const paginationBtn = (disabled: boolean): React.CSSProperties => ({
  padding: "0.5rem 1.1rem",
  background: disabled ? "transparent" : "var(--surface2)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: disabled ? "var(--muted)" : "var(--text)",
  cursor: disabled ? "not-allowed" : "pointer",
  fontSize: "0.85rem",
  opacity: disabled ? 0.5 : 1,
});
