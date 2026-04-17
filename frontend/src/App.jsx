import './App.css'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { isLoggedIn } from './utils/auth'
import HomePage from './pages/HomePage/HomePage'
import UploadPage from './pages/UploadPage/UploadPage'
import ProcessingPage from './pages/ProcessingPage/ProcessingPage'
import ResultsPage from './pages/ResultsPage'
import AboutPage from './pages/AboutPage/AboutPage'
import GuidePage from './pages/GuidePage/GuidePage'
import HistoryPage from './pages/HistoryPage/HistoryPage'
import LoginPage from './pages/LoginPage/LoginPage'

function RequireAuth({ children }) {
  const location = useLocation()
  if (!isLoggedIn()) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }
  return children
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<RequireAuth><HomePage /></RequireAuth>} />
      <Route path="/upload" element={<RequireAuth><UploadPage /></RequireAuth>} />
      <Route path="/processing/:jobId" element={<RequireAuth><ProcessingPage /></RequireAuth>} />
      <Route path="/results/:jobId" element={<RequireAuth><ResultsPage /></RequireAuth>} />
      <Route path="/about" element={<RequireAuth><AboutPage /></RequireAuth>} />
      <Route path="/guide" element={<RequireAuth><GuidePage /></RequireAuth>} />
      <Route path="/history" element={<RequireAuth><HistoryPage /></RequireAuth>} />
    </Routes>
  )
}

export default App
