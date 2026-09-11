import { useCallback, useEffect, useState } from "react";
import api from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

// Quebra "A10, A11, A12" (ou separado por espaço/quebra de linha) em ["A10","A11","A12"].
function parseNumeros(texto) {
  return texto
    .split(/[,\n]+/)
    .map((n) => n.trim())
    .filter(Boolean);
}

// Gera números de apto no padrão comum de prédio: andar 1 → 101,102,103...,
// andar 2 → 201,202,203... (posição sempre com 2 dígitos, começando em 01).
function gerarNumerosPorAndar({ andarInicial, andarFinal, aptosPorAndar }) {
  const andarIni = Number(andarInicial);
  const andarFim = Number(andarFinal);
  const qtd = Number(aptosPorAndar);

  if (!Number.isInteger(andarIni) || !Number.isInteger(andarFim) || andarFim < andarIni) return [];
  if (!Number.isInteger(qtd) || qtd < 1) return [];

  const numeros = [];
  for (let andar = andarIni; andar <= andarFim; andar++) {
    for (let posicao = 1; posicao <= qtd; posicao++) {
      numeros.push(`${andar}${String(posicao).padStart(2, "0")}`);
    }
  }
  return numeros;
}

export default function UnidadesPage() {
  const { user } = useAuth();
  const isSindico = user.papel === "sindico";

  const [condominios, setCondominios] = useState([]);
  const [blocos, setBlocos] = useState([]);
  const [unidades, setUnidades] = useState([]);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(true);

  // Forms (só usados pelo síndico)
  const [novoBlocoNome, setNovoBlocoNome] = useState("");
  const [novaUnidade, setNovaUnidade] = useState({
    modo: "andares", // "andares" (gera por andar) ou "lista" (números avulsos)
    numeros: "",
    blocoId: "",
    andarInicial: "1",
    andarFinal: "1",
    aptosPorAndar: "4",
  });
  const [blocoEmEdicao, setBlocoEmEdicao] = useState(null); // { id, nome }
  const [unidadeConfirmandoRemocao, setUnidadeConfirmandoRemocao] = useState(null); // id

  const numerosGerados =
    novaUnidade.modo === "andares" ? gerarNumerosPorAndar(novaUnidade) : parseNumeros(novaUnidade.numeros);

  const carregarDados = useCallback(async () => {
    setErro("");
    try {
      const [blocosRes, unidadesRes, condominiosRes] = await Promise.all([
        api.get("/blocos"),
        api.get("/unidades"),
        isSindico ? api.get("/condominios") : Promise.resolve({ data: [] }),
      ]);
      setBlocos(blocosRes.data);
      setUnidades(unidadesRes.data);
      setCondominios(condominiosRes.data);
    } catch (err) {
      setErro(err.response?.data?.erro || "Erro ao carregar dados.");
    } finally {
      setCarregando(false);
    }
  }, [isSindico]);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);

  async function handleCriarBloco(e) {
    e.preventDefault();
    const condominioId = condominios[0]?.id;
    if (!condominioId) {
      setErro("Nenhum condomínio disponível para vincular o bloco.");
      return;
    }
    try {
      await api.post("/blocos", { nome: novoBlocoNome, condominioId });
      setNovoBlocoNome("");
      await carregarDados();
    } catch (err) {
      setErro(err.response?.data?.erro || "Erro ao criar bloco.");
    }
  }

  async function handleSalvarEdicaoBloco(e) {
    e.preventDefault();
    const nome = blocoEmEdicao.nome.trim();
    if (!nome) return;
    try {
      await api.put(`/blocos/${blocoEmEdicao.id}`, { nome });
      setBlocoEmEdicao(null);
      await carregarDados();
    } catch (err) {
      setErro(err.response?.data?.erro || "Erro ao editar bloco.");
    }
  }

  async function handleCriarUnidade(e) {
    e.preventDefault();
    if (numerosGerados.length === 0 || !novaUnidade.blocoId) {
      setErro("Informe ao menos um número de unidade e o bloco.");
      return;
    }
    try {
      // O hidrômetro de cada unidade é criado automaticamente pelo backend.
      await api.post("/unidades", { numeros: numerosGerados, blocoId: novaUnidade.blocoId });
      setNovaUnidade((s) => ({ ...s, numeros: "" }));
      await carregarDados();
    } catch (err) {
      setErro(err.response?.data?.erro || "Erro ao criar unidade(s).");
    }
  }

  // Confirmação inline em vez de `confirm()` nativo, pra manter o mesmo
  // visual do resto da tela em vez de um popup do navegador.
  async function handleRemoverUnidade(id) {
    try {
      await api.delete(`/unidades/${id}`);
      setUnidadeConfirmandoRemocao(null);
      await carregarDados();
    } catch (err) {
      setErro(err.response?.data?.erro || "Erro ao remover unidade.");
    }
  }

  if (carregando) return <div className="page">Carregando...</div>;

  return (
    <div className="page">
      <h1>Unidades</h1>
      <p className="muted">
        {isSindico
          ? "Visão do síndico: todas as unidades do condomínio administrado."
          : "Visão do morador: apenas a(s) sua(s) unidade(s)."}
      </p>

      {erro && <p className="erro">{erro}</p>}

      {isSindico && (
        <section className="card">
          <h2>Cadastrar</h2>
          <div className="forms-row">
            <form onSubmit={handleCriarBloco}>
              <label>
                Novo bloco
                <input
                  value={novoBlocoNome}
                  onChange={(e) => setNovoBlocoNome(e.target.value)}
                  placeholder="Nome do bloco"
                  required
                />
              </label>
              <button type="submit">Adicionar bloco</button>
            </form>

            <form onSubmit={handleCriarUnidade} className="form-unidades">
              <span className="label-titulo">Nova(s) unidade(s)</span>

              <div className="modo-toggle">
                <label className="radio-inline">
                  <input
                    type="radio"
                    checked={novaUnidade.modo === "andares"}
                    onChange={() => setNovaUnidade((s) => ({ ...s, modo: "andares" }))}
                  />
                  Por andar
                </label>
                <label className="radio-inline">
                  <input
                    type="radio"
                    checked={novaUnidade.modo === "lista"}
                    onChange={() => setNovaUnidade((s) => ({ ...s, modo: "lista" }))}
                  />
                  Lista manual
                </label>
              </div>

              {novaUnidade.modo === "andares" ? (
                <div className="andares-grid">
                  <label>
                    Andar inicial
                    <input
                      type="number"
                      min="0"
                      value={novaUnidade.andarInicial}
                      onChange={(e) => setNovaUnidade((s) => ({ ...s, andarInicial: e.target.value }))}
                      required
                    />
                  </label>
                  <label>
                    Andar final
                    <input
                      type="number"
                      min="0"
                      value={novaUnidade.andarFinal}
                      onChange={(e) => setNovaUnidade((s) => ({ ...s, andarFinal: e.target.value }))}
                      required
                    />
                  </label>
                  <label>
                    Aptos por andar
                    <input
                      type="number"
                      min="1"
                      value={novaUnidade.aptosPorAndar}
                      onChange={(e) => setNovaUnidade((s) => ({ ...s, aptosPorAndar: e.target.value }))}
                      required
                    />
                  </label>
                </div>
              ) : (
                <label>
                  Números
                  <input
                    value={novaUnidade.numeros}
                    onChange={(e) => setNovaUnidade((s) => ({ ...s, numeros: e.target.value }))}
                    placeholder="Ex: A04, A05, A06"
                    required
                  />
                </label>
              )}

              <p className="muted small">
                {numerosGerados.length === 0
                  ? "Nenhuma unidade a criar ainda."
                  : `${numerosGerados.length} unidade(s): ${numerosGerados.slice(0, 8).join(", ")}${
                      numerosGerados.length > 8 ? "..." : ""
                    }`}
              </p>

              <label>
                Bloco
                <select
                  value={novaUnidade.blocoId}
                  onChange={(e) => setNovaUnidade((s) => ({ ...s, blocoId: e.target.value }))}
                  required
                >
                  <option value="">Selecione...</option>
                  {blocos.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.nome}
                    </option>
                  ))}
                </select>
              </label>
              <button type="submit">Adicionar unidade(s)</button>
              <span className="muted small">
                O hidrômetro de cada unidade é criado automaticamente.
              </span>
            </form>
          </div>
        </section>
      )}

      {blocos.map((bloco) => {
        const unidadesDoBloco = unidades.filter((u) => u.blocoId === bloco.id);
        return (
          <section key={bloco.id} className="card">
            {blocoEmEdicao?.id === bloco.id ? (
              <form className="edicao-bloco" onSubmit={handleSalvarEdicaoBloco}>
                <input
                  value={blocoEmEdicao.nome}
                  onChange={(e) => setBlocoEmEdicao((s) => ({ ...s, nome: e.target.value }))}
                  autoFocus
                  required
                />
                <button type="submit">Salvar</button>
                <button type="button" className="link" onClick={() => setBlocoEmEdicao(null)}>
                  cancelar
                </button>
              </form>
            ) : (
              <h2>
                {bloco.nome}
                {isSindico && (
                  <button
                    className="link"
                    onClick={() => setBlocoEmEdicao({ id: bloco.id, nome: bloco.nome })}
                  >
                    editar
                  </button>
                )}
              </h2>
            )}
            {unidadesDoBloco.length === 0 ? (
              <p className="muted">Nenhuma unidade cadastrada neste bloco ainda.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Unidade</th>
                    <th>Hidrômetro</th>
                    {isSindico && <th></th>}
                  </tr>
                </thead>
                <tbody>
                  {unidadesDoBloco.map((u) => (
                    <tr key={u.id}>
                      <td>{u.numero}</td>
                      <td>
                        {u.hidrometros.map((h) => (
                          <div key={h.id} className="hidrometro-item">
                            {h.numeroSerie} ({h.litrosPorPulso} L/pulso)
                          </div>
                        ))}
                      </td>
                      {isSindico && (
                        <td>
                          {unidadeConfirmandoRemocao === u.id ? (
                            <span className="confirmacao-remocao">
                              remover mesmo?
                              <button className="link" onClick={() => handleRemoverUnidade(u.id)}>
                                sim
                              </button>
                              <button className="link" onClick={() => setUnidadeConfirmandoRemocao(null)}>
                                não
                              </button>
                            </span>
                          ) : (
                            <button className="link" onClick={() => setUnidadeConfirmandoRemocao(u.id)}>
                              remover unidade
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        );
      })}

      {blocos.length === 0 && <p className="muted">Nenhum bloco cadastrado ainda.</p>}
    </div>
  );
}
