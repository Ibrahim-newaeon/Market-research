/**
 * JWT helpers: signed access (15m) + refresh (7d). Secret pulled from
 * env — never hardcoded. `verify` is a thin timing-safe wrapper.
 */
import jwt, { type SignOptions, type JwtPayload } from "jsonwebtoken";

const ACCESS_TTL = process.env.JWT_ACCESS_TTL ?? "15m";
const REFRESH_TTL = process.env.JWT_REFRESH_TTL ?? "7d";

function secret(): string {
  const s = process.env.JWT_SECRET;
  if (!s || s.length < 32) {
    throw new Error("JWT_SECRET missing or too short (>=32 chars required)");
  }
  return s;
}

export type TokenKind = "access" | "refresh";

export interface PrincipalClaims extends JwtPayload {
  sub: string;            // principal id
  kind: TokenKind;
  preferred_language: "ar" | "en";
}

export function signToken(
  claims: Omit<PrincipalClaims, "iat" | "exp">,
  opts: SignOptions = {}
): string {
  const ttl = claims.kind === "refresh" ? REFRESH_TTL : ACCESS_TTL;
  return jwt.sign(claims, secret(), {
    algorithm: "HS256",
    expiresIn: ttl,
    ...opts,
  });
}

export function verifyToken(token: string, expected: TokenKind): PrincipalClaims {
  const decoded = jwt.verify(token, secret(), { algorithms: ["HS256"] }) as PrincipalClaims;
  if (decoded.kind !== expected) {
    throw new Error(`token kind mismatch: got ${decoded.kind}, expected ${expected}`);
  }
  return decoded;
}

export function rotatePair(sub: string, lang: "ar" | "en"): { access: string; refresh: string } {
  return {
    access: signToken({ sub, kind: "access", preferred_language: lang }),
    refresh: signToken({ sub, kind: "refresh", preferred_language: lang }),
  };
}
