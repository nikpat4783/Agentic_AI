import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { token, ready } = useAuth();

  if (!ready) return null;
  if (!token) return <Navigate to="/login" replace />;
  return children;
}
