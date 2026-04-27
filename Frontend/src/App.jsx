import { Routes, Route, Navigate } from 'react-router-dom'
import AnalysisPage from './pages/AnalysisPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/analyze" replace />} />
      <Route path="/analyze" element={<AnalysisPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
    </Routes>
  )
}

export default App
