import { Pool, PoolConfig } from "pg";

let pool: Pool | null = null;

export function getPool(): Pool {
  if (pool) return pool;
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    throw new Error("DATABASE_URL is required");
  }
  const cfg: PoolConfig = {
    connectionString,
    max: Number(process.env.PGPOOL_MAX ?? 10),
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
    ssl:
      process.env.PGSSLMODE && process.env.PGSSLMODE !== "disable"
        ? { rejectUnauthorized: false }
        : undefined,
  };
  pool = new Pool(cfg);
  pool.on("error", (err) => {
    // eslint-disable-next-line no-console
    console.error("[pg pool] unexpected error", err);
  });
  return pool;
}

export async function closePool(): Promise<void> {
  if (!pool) return;
  await pool.end();
  pool = null;
}

/**
 * Safe parameterized query helper. NEVER interpolate user input into
 * the SQL string — use $1, $2, ... and pass values in params.
 */
export async function query<T extends Record<string, unknown> = Record<string, unknown>>(
  text: string,
  params: readonly unknown[] = []
): Promise<T[]> {
  const p = getPool();
  const res = await p.query<T>(text, params as unknown[]);
  return res.rows;
}

export async function withTx<T>(fn: (client: Awaited<ReturnType<Pool["connect"]>>) => Promise<T>): Promise<T> {
  const client = await getPool().connect();
  try {
    await client.query("BEGIN");
    const out = await fn(client);
    await client.query("COMMIT");
    return out;
  } catch (err) {
    try {
      await client.query("ROLLBACK");
    } catch {
      /* swallow */
    }
    throw err;
  } finally {
    client.release();
  }
}
