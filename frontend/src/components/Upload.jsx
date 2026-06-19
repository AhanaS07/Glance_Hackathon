import { useRef, useState } from 'react'
import { UploadCloud, FileText, Loader2, AlertCircle } from 'lucide-react'
import { analyzeCSV } from '../api'

// Drag-and-drop / click-to-browse upload screen.
// On a successful analysis it calls onSuccess(data) to advance to the dashboard.
export default function Upload({ onSuccess, loading, setLoading, error, setError }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [fileName, setFileName] = useState(null)

  // Validate and analyze a chosen file.
  const handleFile = async (file) => {
    if (!file) return

    // Only accept .csv files.
    const isCsv =
      file.type === 'text/csv' || file.name.toLowerCase().endsWith('.csv')
    if (!isCsv) {
      setError('Please select a valid .csv file.')
      return
    }

    setFileName(file.name)
    setError(null)
    setLoading(true)
    try {
      const data = await analyzeCSV(file)
      onSuccess(data)
    } catch (err) {
      setError(err.message || 'Something went wrong while analyzing the file.')
    } finally {
      setLoading(false)
    }
  }

  // ---- Drag and drop handlers ----
  const onDragOver = (e) => {
    e.preventDefault()
    if (!loading) setDragging(true)
  }
  const onDragLeave = (e) => {
    e.preventDefault()
    setDragging(false)
  }
  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    if (loading) return
    const file = e.dataTransfer.files?.[0]
    handleFile(file)
  }

  // Click on the card opens the hidden file input.
  const onCardClick = () => {
    if (!loading) inputRef.current?.click()
  }

  const onInputChange = (e) => {
    const file = e.target.files?.[0]
    handleFile(file)
    // Reset so selecting the same file again still triggers change.
    e.target.value = ''
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          CSV Insights Dashboard
        </h1>
        <p className="text-gray-400 mt-2 max-w-md mx-auto">
          Upload a CSV file to instantly generate charts and AI-powered insights.
        </p>
      </div>

      {/* Upload card */}
      <div className="w-full max-w-xl">
        <div
          onClick={onCardClick}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          role="button"
          tabIndex={0}
          className={`bg-card rounded-2xl border-2 border-dashed transition-colors duration-200 p-10 text-center cursor-pointer select-none
            ${dragging ? 'border-blue-500 bg-blue-500/5' : 'border-gray-700 hover:border-gray-500'}
            ${loading ? 'pointer-events-none opacity-80' : ''}`}
        >
          {/* Hidden native file input */}
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={onInputChange}
          />

          {loading ? (
            // Loading state while waiting for the API response.
            <div className="flex flex-col items-center gap-3 py-4">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
              <p className="text-gray-300 font-medium">Analyzing your CSV…</p>
              {fileName && (
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  <FileText className="w-4 h-4" /> {fileName}
                </p>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <div className="p-4 rounded-full bg-blue-500/10">
                <UploadCloud className="w-10 h-10 text-blue-500" />
              </div>
              <div>
                <p className="text-lg font-medium text-white">
                  Drag &amp; drop your CSV here
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  or <span className="text-blue-400">click to browse</span>
                </p>
              </div>
              <p className="text-xs text-gray-600">Only .csv files are supported</p>
            </div>
          )}
        </div>

        {/* Inline error message */}
        {error && (
          <div className="mt-4 flex items-start gap-2 rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  )
}
