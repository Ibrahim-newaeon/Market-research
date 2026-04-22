/**
 * Express middleware: JWT bearer auth + strict Helmet CSP + shared
 * rate limiter. Compose in the order (helmet, rateLimit, requireAuth).
 */
import { timingSafeEqual } from "node:crypto";
import type { Request, Response, NextFunction } from "express";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import { verifyToken, type PrincipalClaims } from "./jwt";

// ─── Helmet (strict CSP) ─────────────────────────────────────────────
export const helmetStrict = helmet({
  contentSecurityPolicy: {
    useDefaults: true,
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"], // shadcn utility classes
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://graph.facebook.com"],
      frameAncestors: ["'none'"],
      objectSrc: ["'none'"],
      upgradeInsecureRequests: [],
    },
  },
  crossOriginEmbedderPolicy: false,
  referrerPolicy: { policy: "no-referrer" },
  hsts: { maxAge: 63072000, includeSubDomains: true, preload: true },
});

// ─── Rate limit (default 60/min) ─────────────────────────────────────
const API_LIMIT = Number(process.env.API_RATE_LIMIT_PER_MIN ?? 60);
export const apiRateLimit = rateLimit({
  windowMs: 60_000,
  max: API_LIMIT,
  standardHeaders: true,
  legacyHeaders: false,
  message: { ok: false, code: "rate_limited" },
});

// ─── Auth ────────────────────────────────────────────────────────────
declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Express {
    interface Request {
      principal?: PrincipalClaims;
    }
  }
}

export function requireAuth(req: Request, res: Response, next: NextFunction): void {
  try {
    const header = req.header("authorization") ?? "";
    const [scheme, token] = header.split(" ");
    if (scheme !== "Bearer" || !token) {
      res.status(401).json({ ok: false, code: "missing_bearer" });
      return;
    }
    req.principal = verifyToken(token, "access");
    next();
  } catch (err) {
    res.status(401).json({ ok: false, code: "invalid_token", detail: (err as Error).message });
  }
}

// ─── Principal token (lightweight shared-secret for mutating routes) ─
// Policy — env-driven so enabling it is a Railway config change, not a code push:
//   PRINCIPAL_ACCESS_TOKEN=<secret>          → enable the gate
//   MOI_REQUIRE_PRINCIPAL_TOKEN=true         → fail-closed even if token unset
// When PRINCIPAL_ACCESS_TOKEN is unset AND MOI_REQUIRE_PRINCIPAL_TOKEN is not
// "true", the middleware passes through (backward-compatible; matches the
// current open posture). Accepts the secret via `x-principal-token` header
// OR a `principal_token` cookie (set by GET /api/auth/login).

const COOKIE_NAME = "principal_token";

function readCookie(req: Request, name: string): string | null {
  const raw = req.headers.cookie;
  if (!raw) return null;
  for (const part of raw.split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === name) return decodeURIComponent(rest.join("="));
  }
  return null;
}

function constantTimeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  return timingSafeEqual(Buffer.from(a, "utf8"), Buffer.from(b, "utf8"));
}

export function requirePrincipal(req: Request, res: Response, next: NextFunction): void {
  const expected = process.env.PRINCIPAL_ACCESS_TOKEN;
  const enforce = String(process.env.MOI_REQUIRE_PRINCIPAL_TOKEN ?? "").toLowerCase() === "true";

  if (!expected) {
    if (enforce) {
      res.status(503).json({
        ok: false,
        code: "auth_not_configured",
        detail: "PRINCIPAL_ACCESS_TOKEN env var is required",
      });
      return;
    }
    return next();
  }

  const provided = req.header("x-principal-token") ?? readCookie(req, COOKIE_NAME);
  if (!provided) {
    res.status(401).json({ ok: false, code: "missing_principal_token" });
    return;
  }
  if (!constantTimeEqual(provided, expected)) {
    res.status(401).json({ ok: false, code: "invalid_principal_token" });
    return;
  }
  next();
}

/**
 * Exchange the token in ?token= for a same-origin HttpOnly cookie, then
 * redirect to ?next= (default "/"). Intended as a one-time bootstrap:
 *   https://<host>/api/auth/login?token=<secret>&next=/overview
 * After this, the dashboard sends the cookie automatically on every
 * subsequent same-origin fetch.
 */
export function loginHandler(req: Request, res: Response): void {
  const expected = process.env.PRINCIPAL_ACCESS_TOKEN;
  if (!expected) {
    res.status(503).json({ ok: false, code: "auth_not_configured" });
    return;
  }
  const token = typeof req.query.token === "string" ? req.query.token : "";
  if (!token) {
    res.status(400).json({ ok: false, code: "token_required" });
    return;
  }
  if (!constantTimeEqual(token, expected)) {
    res.status(401).json({ ok: false, code: "invalid_principal_token" });
    return;
  }
  const next = typeof req.query.next === "string" && req.query.next.startsWith("/") ? req.query.next : "/";
  const secure = req.secure || req.header("x-forwarded-proto") === "https";
  const maxAgeDays = 30;
  res.setHeader(
    "set-cookie",
    [
      `${COOKIE_NAME}=${encodeURIComponent(token)}`,
      `Max-Age=${maxAgeDays * 24 * 3600}`,
      "Path=/",
      "HttpOnly",
      "SameSite=Lax",
      secure ? "Secure" : "",
    ]
      .filter(Boolean)
      .join("; ")
  );
  res.redirect(302, next);
}

/**
 * Clears the principal_token cookie. Logs out on this device.
 */
export function logoutHandler(_req: Request, res: Response): void {
  res.setHeader(
    "set-cookie",
    `${COOKIE_NAME}=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax`
  );
  res.json({ ok: true });
}

// ─── Error handler (last) ────────────────────────────────────────────
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function errorHandler(err: unknown, _req: Request, res: Response, _next: NextFunction): void {
  const message = err instanceof Error ? err.message : "unknown";
  // eslint-disable-next-line no-console
  console.error("[api] unhandled", err);
  res.status(500).json({ ok: false, code: "internal", detail: message });
}
