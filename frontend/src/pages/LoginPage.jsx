import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setErro("");
    setCarregando(true);
    try {
      await login(email, senha);
      navigate("/unidades");
    } catch (err) {
      setErro(err.response?.data?.erro || "Não foi possível entrar. Verifique suas credenciais.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="page page--center">
      <form className="card" onSubmit={handleSubmit}>
        <h1>HidroMeter</h1>
        <p className="muted">Entre com seu email e senha.</p>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </label>

        <label>
          Senha
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
          />
        </label>

        {erro && <p className="erro">{erro}</p>}

        <button type="submit" disabled={carregando}>
          {carregando ? "Entrando..." : "Entrar"}
        </button>

        <p className="muted small">Demo: sindico@hidrometer.com — senha: senha123</p>
      </form>
    </div>
  );
}
