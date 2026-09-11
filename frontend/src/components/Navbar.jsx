import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="navbar">
      <span className="navbar__brand">HidroMeter</span>
      <span className="navbar__user">
        {user.nome} <em>({user.papel})</em>
      </span>
      <button onClick={handleLogout}>Sair</button>
    </header>
  );
}
