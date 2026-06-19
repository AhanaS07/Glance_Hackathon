import { useState } from 'react'
import Upload from './components/Upload'
import Dashboard from './components/Dashboard'

// Root component. Owns the top-level application state and switches between
// the upload screen and the dashboard screen.
export default function App() {
  const [view, setView] = useState('upload') // "upload" | "dashboard"
  const [data, setData] = useState(null) // full API response
  const [loading, setLoading] = useState(false) // request in flight
  const [error, setError] = useState(null) // error message string

  // Called by Upload when the analysis request succeeds.
  const handleSuccess = (responseData) => {
    setData(responseData)
    setError(null)
    setView('dashboard')
  }

  // Reset everything and return to the upload screen.
  const handleReset = () => {
    setData(null)
    setError(null)
    setLoading(false)
    setView('upload')
  }

  return (
    <div className="min-h-screen bg-base text-white">
      {view === 'upload' ? (
        <Upload
          onSuccess={handleSuccess}
          loading={loading}
          setLoading={setLoading}
          error={error}
          setError={setError}
        />
      ) : (
        <Dashboard data={data} onReset={handleReset} />
      )}
    </div>
  )
}
