import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import PrivateRoute from "./components/PrivateRoute.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ConsumoPage from "./pages/ConsumoPage.jsx";
import UnidadesPage from "./pages/UnidadesPage.jsx";

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/unidades"
          element={
            <PrivateRoute>
              <UnidadesPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/consumo"
          element={
            <PrivateRoute>
              <ConsumoPage />
            </PrivateRoute>
          }
        />
        <Route path="/" element={<Navigate to="/unidades" replace />} />
        <Route path="*" element={<Navigate to="/unidades" replace />} />
      </Routes>
    </>
  );
}
