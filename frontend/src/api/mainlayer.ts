/**
 * Mainlayer Agent Marketplace — API client
 *
 * All calls go through the backend FastAPI server which holds the
 * Mainlayer API key. The frontend never touches the Mainlayer API directly.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

// ---------------------------------------------------------------------------
// Types (mirrors backend Pydantic models)
// ---------------------------------------------------------------------------

export interface AgentCapability {
  name: string;
  description: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  category: string;
  price_per_call: number;
  currency: string;
  capabilities: AgentCapability[];
  tags: string[];
  example_input: string | null;
  example_output: string | null;
  resource_id: string;
  publisher_id: string;
  created_at: string;
  call_count: number;
  rating: number | null;
}

export interface AgentListResponse {
  agents: Agent[];
  total: number;
  limit: number;
  offset: number;
}

export interface RunAgentRequest {
  payer_api_key: string;
  input_data: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface RunAgentResponse {
  payment_id: string;
  payment_status: string;
  agent_id: string;
  output: unknown;
  credits_used: number;
  currency: string;
}

export interface EntitlementResponse {
  entitled: boolean;
  calls_remaining: number;
  resource_id: string;
  payer_api_key: string;
}

export interface PublishAgentRequest {
  name: string;
  description: string;
  category: string;
  price_per_call: number;
  capabilities: AgentCapability[];
  tags: string[];
  example_input?: string;
  example_output?: string;
}

export interface MarketplaceStats {
  total_agents: number;
  total_calls: number;
  categories: { category: string; count: number }[];
  featured_agent_ids: string[];
}

export interface DiscoverParams {
  query?: string;
  category?: string;
  tags?: string[];
  min_price?: number;
  max_price?: number;
  sort_by?: "created_at" | "price_per_call" | "call_count";
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  method: string,
  path: string,
  options: { json?: unknown; params?: Record<string, string | number | boolean | string[]> } = {}
): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`);
  if (options.params) {
    for (const [key, value] of Object.entries(options.params)) {
      if (value === undefined || value === null) continue;
      if (Array.isArray(value)) {
        value.forEach((v) => url.searchParams.append(key, String(v)));
      } else {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const res = await fetch(url.toString(), {
    method,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: options.json !== undefined ? JSON.stringify(options.json) : undefined,
  });

  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    throw new ApiError(res.status, `API error ${res.status}`, detail);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Agent API
// ---------------------------------------------------------------------------

export const agentsApi = {
  list: (limit = 20, offset = 0) =>
    request<AgentListResponse>("GET", "/agents", { params: { limit, offset } }),

  get: (agentId: string) =>
    request<Agent>("GET", `/agents/${agentId}`),

  publish: (body: PublishAgentRequest) =>
    request<Agent>("POST", "/agents", { json: body }),
};

// ---------------------------------------------------------------------------
// Marketplace / Discovery API
// ---------------------------------------------------------------------------

export const marketplaceApi = {
  discover: (params: DiscoverParams = {}) => {
    const { tags, ...rest } = params;
    return request<AgentListResponse>("GET", "/marketplace/discover", {
      params: { ...rest, ...(tags && tags.length > 0 ? { tags } : {}) } as Record<string, string | number | boolean | string[]>,
    });
  },

  stats: () => request<MarketplaceStats>("GET", "/marketplace/stats"),

  categories: () => request<string[]>("GET", "/marketplace/categories"),
};

// ---------------------------------------------------------------------------
// Payments API
// ---------------------------------------------------------------------------

export const paymentsApi = {
  runAgent: (agentId: string, body: RunAgentRequest) =>
    request<RunAgentResponse>("POST", `/payments/agents/${agentId}/run`, { json: body }),

  checkEntitlement: (agentId: string, payerApiKey: string) =>
    request<EntitlementResponse>("GET", `/payments/agents/${agentId}/entitlement`, {
      params: { payer_api_key: payerApiKey },
    }),
};

export { ApiError };
