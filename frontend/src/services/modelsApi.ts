import type { ModelListResponse } from "@/types/api";
import type { CatalogModel } from "@/types/models";
import { request } from "./apiClient";

/** Catálogo de modelos con su precio vigente (GET /models). */
export async function getModels(signal?: AbortSignal): Promise<CatalogModel[]> {
  const data = await request<ModelListResponse>("/models", { signal });

  return data.models.map((model) => ({
    id: model.id,
    provider: model.provider,
    modelKey: model.model_key,
    displayName: model.display_name,
    contextWindow: model.context_window,
    active: model.active,
    currentPrice: model.current_price && {
      inputCostPerMillion: model.current_price.input_cost_per_million,
      outputCostPerMillion: model.current_price.output_cost_per_million,
      currency: model.current_price.currency,
    },
  }));
}
