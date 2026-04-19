/**
 * Dashboard API client. Reads the DashboardPayload produced by
 * dashboard_aggregator_agent. Never writes. Gracefully handles empty
 * state and tab-scoped requests.
 */
import type { DashboardPayload, TabSlug } from "@schemas/dashboard";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:3000";

export type TabData = DashboardPayload["tabs"][TabSlug];

export interface EmptyDashboard {
  status: "empty";
  reason: string;
}

export function isEmpty(p: DashboardPayload | EmptyDashboard): p is EmptyDashboard {
  return (p as EmptyDashboard).status === "empty";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`api ${path} ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

export async function getDashboard(): Promise<DashboardPayload | EmptyDashboard> {
  return request<DashboardPayload | EmptyDashboard>("/api/dashboard");
}

export async function getTab(tab: TabSlug): Promise<TabData | EmptyDashboard> {
  return request<TabData | EmptyDashboard>(`/api/dashboard/${tab}`);
}
