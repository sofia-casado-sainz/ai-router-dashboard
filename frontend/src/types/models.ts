/** Modelo del catálogo persistente; todos los campos vienen de GET /models. */
export interface CatalogModel {
  id: string;
  provider: string;
  modelKey: string;
  displayName: string;
  contextWindow: number;
  active: boolean;
  /** null si el modelo no tiene precio vigente. */
  currentPrice: ModelPrice | null;
}

export interface ModelPrice {
  inputCostPerMillion: number;
  outputCostPerMillion: number;
  currency: string;
}
