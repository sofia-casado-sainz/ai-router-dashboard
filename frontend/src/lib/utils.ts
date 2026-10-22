/** Une clases condicionales de Tailwind sin dependencias externas. */
export function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}
