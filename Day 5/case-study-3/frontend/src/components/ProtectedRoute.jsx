import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

// Gates a route on the session being authenticated. Unauthenticated users
// are bounced to /login instead of hitting a 401 from the backend.
export default function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}
