export default function StatsCards() {
  return (
    <div className="grid grid-cols-3 gap-4">

      <div className="bg-zinc-900 p-6 rounded-xl">
        <h2>Coste mes</h2>
        <p className="text-2xl font-bold">
          0 €
        </p>
      </div>

      <div className="bg-zinc-900 p-6 rounded-xl">
        <h2>Consultas</h2>
        <p className="text-2xl font-bold">
          0
        </p>
      </div>

      <div className="bg-zinc-900 p-6 rounded-xl">
        <h2>Modelo favorito</h2>
        <p className="text-2xl font-bold">
          Ninguno
        </p>
      </div>

    </div>
  );
}