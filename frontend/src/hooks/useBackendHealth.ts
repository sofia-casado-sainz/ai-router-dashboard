"use client";

import { useEffect, useState } from "react";
import { checkHealth } from "@/services/routerApi";

export type BackendStatus = "checking" | "online" | "offline";

const POLL_INTERVAL_MS = 30_000;

/** Consulta GET /health al montar y cada 30 s. */
export function useBackendHealth() {
  const [status, setStatus] = useState<BackendStatus>("checking");

  useEffect(() => {
    const controller = new AbortController();

    const check = async () => {
      const ok = await checkHealth(controller.signal);
      if (!controller.signal.aborted) setStatus(ok ? "online" : "offline");
    };

    void check();
    const interval = setInterval(check, POLL_INTERVAL_MS);
    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, []);

  return status;
}
