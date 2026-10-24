"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/services/apiClient";
import { getModels } from "@/services/modelsApi";
import type { CatalogModel } from "@/types/models";

type CatalogState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; models: CatalogModel[] };

/** Carga el catálogo de modelos al montar; `reload` lo vuelve a pedir tras un error. */
export function useModelCatalog() {
  const [state, setState] = useState<CatalogState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    getModels(controller.signal)
      .then((models) => setState({ status: "ready", models }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof ApiError ? error.message : "Error inesperado al cargar el catálogo.",
        });
      });

    return () => controller.abort();
  }, [attempt]);

  const reload = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((n) => n + 1);
  }, []);

  return { state, reload };
}
