import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import Marketplace from "./pages/Marketplace";
import AgentDetail from "./pages/AgentDetail";
import Publish from "./pages/Publish";

function NavBar() {
  const location = useLocation();

  const isActive = (path: string) =>
    path === "/"
      ? location.pathname === "/"
      : location.pathname.startsWith(path);

  return (
    <nav
      style={{
        background: "var(--surface)",
        borderBottom: "1px solid var(--border)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        backdropFilter: "blur(8px)",
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "0 1.5rem",
          height: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Logo */}
        <Link
          to="/"
          style={{
            textDecoration: "none",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <span
            style={{
              width: 30,
              height: 30,
              background: "var(--brand)",
              borderRadius: 8,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1rem",
            }}
          >
            🤖
          </span>
          <span style={{ fontWeight: 800, fontSize: "1rem", color: "var(--text)" }}>
            AgentMarket
          </span>
        </Link>

        {/* Nav links */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
          <NavLink to="/" label="Marketplace" active={isActive("/")} />
          <NavLink to="/publish" label="Publish Agent" active={isActive("/publish")} highlight />
        </div>
      </div>
    </nav>
  );
}

function NavLink({
  to,
  label,
  active,
  highlight = false,
}: {
  to: string;
  label: string;
  active: boolean;
  highlight?: boolean;
}) {
  return (
    <Link
      to={to}
      style={{
        textDecoration: "none",
        padding: "0.4rem 0.9rem",
        borderRadius: 8,
        fontSize: "0.875rem",
        fontWeight: highlight ? 700 : 500,
        color: active
          ? "#fff"
          : highlight
          ? "var(--brand)"
          : "var(--muted)",
        background: active
          ? "var(--brand)"
          : highlight && !active
          ? "rgba(99,102,241,0.12)"
          : "transparent",
        border: highlight && !active ? "1px solid rgba(99,102,241,0.3)" : "1px solid transparent",
        transition: "all 0.15s",
      }}
    >
      {label}
    </Link>
  );
}

function Footer() {
  return (
    <footer
      style={{
        borderTop: "1px solid var(--border)",
        padding: "1.5rem",
        textAlign: "center",
        marginTop: "auto",
        color: "var(--muted)",
        fontSize: "0.8rem",
      }}
    >
      Powered by{" "}
      <a
        href="https://mainlayer.fr"
        target="_blank"
        rel="noreferrer"
        style={{ color: "var(--brand)", textDecoration: "none", fontWeight: 600 }}
      >
        Mainlayer
      </a>{" "}
      — payment infrastructure for AI agents
    </footer>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<Marketplace />} />
          <Route path="/agents/:id" element={<AgentDetail />} />
          <Route path="/publish" element={<Publish />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </BrowserRouter>
  );
}

function NotFound() {
  return (
    <div style={{ textAlign: "center", padding: "5rem 1.5rem" }}>
      <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>404</div>
      <p style={{ color: "var(--muted)", marginBottom: "1.5rem" }}>Page not found.</p>
      <Link
        to="/"
        style={{
          padding: "0.6rem 1.4rem",
          background: "var(--brand)",
          color: "#fff",
          textDecoration: "none",
          borderRadius: 8,
          fontWeight: 600,
          fontSize: "0.875rem",
        }}
      >
        Back to Marketplace
      </Link>
    </div>
  );
}
