import './App.css'
import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage/HomePage'
import UploadPage from './pages/UploadPage/UploadPage'
import ProcessingPage from './pages/ProcessingPage/ProcessingPage'
import ResultsPage from './pages/ResultsPage'
import AboutPage from './pages/AboutPage/AboutPage'
import GuidePage from './pages/GuidePage/GuidePage'
import HistoryPage from './pages/HistoryPage/HistoryPage'
import { AuthProvider } from './context/AuthContext'

function App() {
  return (
    <AuthProvider>
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/processing/:jobId" element={<ProcessingPage />} />
      <Route path="/results/:jobId" element={<ResultsPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/guide" element={<GuidePage />} />
      <Route path="/history" element={<HistoryPage />} />
    </Routes>
    </AuthProvider>
  )
}

export default App
