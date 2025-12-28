import { useState } from 'react'
import './App.css'
import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage/HomePage'
import UploadPage from './pages/UploadPage/UploadPage'
import ProcessingPage from './pages/ProcessingPage'
import ResultsPage from './pages/ResultsPage'

function App() {
  const [count, setCount] = useState(0)

  return (
    <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/processing/:jobId" element={<ProcessingPage />} />
        <Route path="/results/:jobId" element={<ResultsPage />} />
    </Routes>
  )
}

export default App
