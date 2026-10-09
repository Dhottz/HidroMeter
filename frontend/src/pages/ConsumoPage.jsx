import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../api/client.js";

const PRESETS = [
  { dias: 7, rotulo: "7 dias" },
  { dias: 30, rotulo: "30 dias" },
  { dias: 90, rotulo: "90 dias" },
];
const MAX_DIAS_POR_HORA = 14; // acima disso são barras demais para ler

const fmtLitros = (v) => `${Math.round(v).toLocaleString("pt-BR")} L`;

function rotuloEixo(iso, agrupar) {
  const d = new Date(iso);
  return agrupar === "hora"
    ? `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}h`
    : `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export default function ConsumoPage() {
  const [unidades, setUnidades] = useState([]);
  const [unidadeId, setUnidadeId] = useState("");
  const [periodo, setPeriodo] = useState({ tipo: "preset", dias: 30, de: "", ate: "" });
  const [agrupar, setAgrupar] = useState("dia");
  const [consumo, setConsumo] = useState(null);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    api
      .get("/unidades")
      .then(({ data }) => {
        setUnidades(data);
        if (data.length) setUnidadeId(String(data[0].id));
      })
      .catch((err) => setErro(err.response?.data?.erro || "Erro ao carregar unidades."))
      .finally(() => setCarregando(false));
  }, []);

  const diasDoPeriodo = useMemo(() => {
    if (periodo.tipo === "preset") return periodo.dias;
    if (!periodo.de || !periodo.ate) return null;
    return Math.ceil((new Date(periodo.ate) - new Date(periodo.de)) / 86400000) + 1;
  }, [periodo]);
  const horaPermitida = diasDoPeriodo !== null && diasDoPeriodo <= MAX_DIAS_POR_HORA;
  const agruparEfetivo = horaPermitida ? agrupar : "dia";

  useEffect(() => {
    if (!unidadeId) return;
    const params = { agrupar: agruparEfetivo };
    if (periodo.tipo === "preset") {
      params.dias = periodo.dias;
    } else {
      if (!periodo.de || !periodo.ate) return;
      params.de = `${periodo.de}T00:00:00`;
      params.ate = `${periodo.ate}T23:59:59`;
    }
    let cancelado = false;
    setErro("");
    api
      .get(`/unidades/${unidadeId}/consumo`, { params })
      .then(({ data }) => !cancelado && setConsumo(data))
      .catch((err) => {
        if (cancelado) return;
        setConsumo(null);
        setErro(err.response?.data?.erro || "Erro ao carregar consumo.");
      });
    return () => {
      cancelado = true;
    };
  }, [unidadeId, periodo, agruparEfetivo]);

  const dados = useMemo(
    () => (consumo?.pontos || []).map((p) => ({ ...p, rotulo: rotuloEixo(p.inicio, consumo.agrupar) })),
    [consumo],
  );
  const resumo = useMemo(() => {
    if (!dados.length) return null;
    const pico = dados.reduce((a, b) => (b.litros > a.litros ? b : a));
    return { total: consumo.totalLitros, media: consumo.totalLitros / dados.length, pico };
  }, [dados, consumo]);

  const porBloco = useMemo(() => {
    const grupos = new Map();
    for (const u of unidades) {
      if (!grupos.has(u.bloco.nome)) grupos.set(u.bloco.nome, []);
      grupos.get(u.bloco.nome).push(u);
    }
    return [...grupos.entries()];
  }, [unidades]);

  if (carregando) return <div className="page">Carregando...</div>;

  return (
    <div className="page">
      <section className="card">
        <h1>Consumo de água</h1>
        {erro && <p className="erro">{erro}</p>}
        {unidades.length === 0 ? (
          <p className="muted">Nenhuma unidade disponível.</p>
        ) : (
          <div className="consumo-filtros">
            <label>
              Unidade
              <select value={unidadeId} onChange={(e) => setUnidadeId(e.target.value)}>
                {porBloco.map(([bloco, lista]) => (
                  <optgroup key={bloco} label={bloco}>
                    {lista.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.numero}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </label>

            <div>
              <span className="label-titulo">Período</span>
              <div className="consumo-botoes">
                {PRESETS.map((p) => (
                  <button
                    key={p.dias}
                    type="button"
                    className={periodo.tipo === "preset" && periodo.dias === p.dias ? "ativo" : ""}
                    onClick={() => setPeriodo({ tipo: "preset", dias: p.dias, de: "", ate: "" })}
                  >
                    {p.rotulo}
                  </button>
                ))}
                <button
                  type="button"
                  className={periodo.tipo === "custom" ? "ativo" : ""}
                  onClick={() => setPeriodo((p) => ({ ...p, tipo: "custom" }))}
                >
                  Personalizado
                </button>
              </div>
              {periodo.tipo === "custom" && (
                <div className="consumo-botoes">
                  <input
                    type="date"
                    value={periodo.de}
                    onChange={(e) => setPeriodo((p) => ({ ...p, de: e.target.value }))}
                  />
                  <span>até</span>
                  <input
                    type="date"
                    value={periodo.ate}
                    onChange={(e) => setPeriodo((p) => ({ ...p, ate: e.target.value }))}
                  />
                </div>
              )}
            </div>

            <div>
              <span className="label-titulo">Agrupar por</span>
              <div className="consumo-botoes">
                <button type="button" className={agruparEfetivo === "dia" ? "ativo" : ""} onClick={() => setAgrupar("dia")}>
                  Dia
                </button>
                <button
                  type="button"
                  className={agruparEfetivo === "hora" ? "ativo" : ""}
                  disabled={!horaPermitida}
                  title={horaPermitida ? "" : `Disponível para períodos de até ${MAX_DIAS_POR_HORA} dias`}
                  onClick={() => setAgrupar("hora")}
                >
                  Hora
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {unidades.length > 0 && (
        <section className="card">
          {resumo && (
            <div className="consumo-resumo">
              <div>
                <span className="muted small">Total no período</span>
                <strong>{fmtLitros(resumo.total)}</strong>
              </div>
              <div>
                <span className="muted small">Média por {agruparEfetivo}</span>
                <strong>{fmtLitros(resumo.media)}</strong>
              </div>
              <div>
                <span className="muted small">Maior consumo</span>
                <strong>
                  {fmtLitros(resumo.pico.litros)} <em className="muted small">({resumo.pico.rotulo})</em>
                </strong>
              </div>
            </div>
          )}

          {dados.length === 0 ? (
            <p className="muted">Sem leituras para esta unidade no período selecionado.</p>
          ) : (
            <div className="consumo-grafico">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dados} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="rotulo" tick={{ fontSize: 11 }} minTickGap={24} />
                  <YAxis tick={{ fontSize: 11 }} unit=" L" width={64} />
                  <Tooltip formatter={(v) => [fmtLitros(v), "Consumo"]} />
                  <Bar dataKey="litros" fill="#0b6fa4" radius={[2, 2, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
