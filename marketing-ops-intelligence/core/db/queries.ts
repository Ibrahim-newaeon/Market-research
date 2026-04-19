/**
 * Parameterized SQL helpers for campaign memory and approval state.
 * Never builds SQL via string concatenation of user input.
 */
import { query, withTx } from "./client";
import type { MemoryEntry } from "../schemas";

export async function listMemoryEntries(marketId?: string): Promise<MemoryEntry[]> {
  if (marketId) {
    return query<MemoryEntry>(
      `SELECT entry_id, created_at, market_id, kind, summary, evidence_ref, confidence
         FROM campaign_memory
        WHERE market_id = $1
        ORDER BY created_at DESC
        LIMIT 500`,
      [marketId]
    );
  }
  return query<MemoryEntry>(
    `SELECT entry_id, created_at, market_id, kind, summary, evidence_ref, confidence
       FROM campaign_memory
      ORDER BY created_at DESC
      LIMIT 500`
  );
}

export async function insertMemoryEntries(entries: MemoryEntry[]): Promise<number> {
  if (entries.length === 0) return 0;
  return withTx(async (client) => {
    let inserted = 0;
    for (const e of entries) {
      const res = await client.query(
        `INSERT INTO campaign_memory
            (entry_id, created_at, market_id, kind, summary, evidence_ref, confidence)
         VALUES ($1,$2,$3,$4,$5,$6,$7)
         ON CONFLICT (entry_id) DO NOTHING`,
        [
          e.entry_id,
          e.created_at,
          e.market_id,
          e.kind,
          e.summary,
          e.evidence_ref,
          e.confidence,
        ]
      );
      inserted += res.rowCount ?? 0;
    }
    return inserted;
  });
}

export async function recordDecision(
  runId: string,
  decision: "approved" | "declined" | "edited" | "timeout",
  reason: string
): Promise<void> {
  await query(
    `INSERT INTO plan_decisions (run_id, decided_at, decision, reason)
     VALUES ($1, NOW(), $2, $3)
     ON CONFLICT (run_id) DO UPDATE SET decision = EXCLUDED.decision, reason = EXCLUDED.reason`,
    [runId, decision, reason]
  );
}

export async function getLatestDashboardPayload(runId: string): Promise<unknown | null> {
  const rows = await query<{ payload: unknown }>(
    `SELECT payload FROM dashboard_payloads WHERE run_id = $1 ORDER BY generated_at DESC LIMIT 1`,
    [runId]
  );
  return rows[0]?.payload ?? null;
}
