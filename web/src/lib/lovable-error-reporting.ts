/**
 * This project started as a Lovable design and kept its error hook. Majlis runs
 * locally, so errors stay in the console rather than being sent anywhere.
 */
export function reportLovableError(error: unknown, context?: Record<string, unknown>): void {
  console.error("[majlis]", context ?? {}, error);
}
