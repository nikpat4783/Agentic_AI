import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import DomainSelectPage from "./pages/DomainSelectPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ResearchChatPage from "./pages/ResearchChatPage";

export default function App() {
  const { token, ready } = useAuth();

  if (!ready) return null;

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/domains" replace /> : <LoginPage />} />
      <Route path="/register" element={token ? <Navigate to="/domains" replace /> : <RegisterPage />} />
      <Route
        path="/domains"
        element={
          <ProtectedRoute>
            <DomainSelectPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/research/:domainId"
        element={
          <ProtectedRoute>
            <ResearchChatPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to={token ? "/domains" : "/login"} replace />} />
    </Routes>
  );
}
