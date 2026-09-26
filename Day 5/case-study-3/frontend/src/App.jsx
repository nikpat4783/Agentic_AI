import { NavLink, Routes, Route, useNavigate } from 'react-router-dom'
import UploadPage from './pages/UploadPage.jsx'
import ExtractionReviewPage from './pages/ExtractionReviewPage.jsx'
import QAQueuePage from './pages/QAQueuePage.jsx'
import SubmissionPage from './pages/SubmissionPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { useAuth } from './context/AuthContext.jsx'

export default function App() {
  const navigate = useNavigate()
  const { isAuthenticated, logout } = useAuth()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">Carta Clinical Data Extraction</span>
        {isAuthenticated && (
          <nav className="app-nav">
            <NavLink to="/" end>
              Upload
            </NavLink>
            <NavLink to="/qa">QA queue</NavLink>
            <button type="button" className="logout-button" onClick={handleLogout}>
              Log out
            </button>
          </nav>
        )}
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <UploadPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review/:documentId"
            element={
              <ProtectedRoute>
                <ExtractionReviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/qa"
            element={
              <ProtectedRoute>
                <QAQueuePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/submission/:documentId"
            element={
              <ProtectedRoute>
                <SubmissionPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  )
}
