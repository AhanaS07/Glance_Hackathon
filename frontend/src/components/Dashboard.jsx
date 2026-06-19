import { RotateCcw, Database, Rows3, Columns3 } from 'lucide-react'
import ChartCard from './ChartCard'
import InsightCard from './InsightCard'

// Dashboard view. Renders the dataset summary, a responsive grid of charts,
// and a list of AI-generated insights.
export default function Dashboard({ data, onReset }) {
  // Guard against a missing response.
  if (!data) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-gray-400">No analysis data available.</p>
        <button
          onClick={onReset}
          className="px-4 py-2 rounded-lg bg-card border border-gray-700 hover:border-gray-500 transition-colors"
        >
          Back to upload
        </button>
      </div>
    )
  }

  // The backend's `summary` is an object { rowCount, columnCount, description,
  // columns }. Stay tolerant of a bare-string summary too, just in case.
  const summaryObj =
    data.summary && typeof data.summary === 'object' ? data.summary : null
  const summaryText = summaryObj
    ? summaryObj.description
    : typeof data.summary === 'string'
      ? data.summary
      : ''
  const totalRows =
    summaryObj?.rowCount ?? data.total_rows ?? data.rows_count ?? data.rowCount
  const totalColumns =
    summaryObj?.columnCount ??
    data.total_columns ??
    data.columns_count ??
    data.columnCount
  const charts = Array.isArray(data.charts) ? data.charts : []
  const insights = Array.isArray(data.insights) ? data.insights : []

  // Charts already carry their aggregated `data[]` from chart_builder.py.
  // rawData is only a fallback for charts that arrive without it.
  const rawData = data.data ?? data.rows ?? data.raw_data ?? []

  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-8 max-w-7xl mx-auto">
      {/* Top bar */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
          CSV Insights Dashboard
        </h1>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-card border border-gray-700 hover:border-gray-500 hover:bg-white/5 transition-colors text-sm font-medium"
        >
          <RotateCcw className="w-4 h-4" />
          Analyze another CSV
        </button>
      </header>

      {/* A. Dataset Summary Card */}
      <section className="bg-card rounded-2xl border border-gray-800 p-6 mb-8">
        <div className="flex items-center gap-2 mb-3 text-gray-300">
          <Database className="w-5 h-5 text-blue-500" />
          <h2 className="text-lg font-semibold">Dataset Summary</h2>
        </div>
        {summaryText && (
          <p className="text-gray-400 leading-relaxed mb-5">{summaryText}</p>
        )}
        <div className="grid grid-cols-2 gap-4 max-w-md">
          <Stat
            icon={<Rows3 className="w-4 h-4" />}
            label="Total Rows"
            value={totalRows ?? '—'}
          />
          <Stat
            icon={<Columns3 className="w-4 h-4" />}
            label="Total Columns"
            value={totalColumns ?? '—'}
          />
        </div>
      </section>

      {/* B. Charts Grid */}
      {charts.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-4">Charts</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {charts.map((chart, idx) => (
              <ChartCard key={idx} chart={chart} rawData={rawData} />
            ))}
          </div>
        </section>
      )}

      {/* C. Insights Section */}
      {insights.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.map((text, idx) => (
              <InsightCard key={idx} text={text} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

// Small stat tile used inside the summary card.
function Stat({ icon, label, value }) {
  return (
    <div className="rounded-xl bg-black/30 border border-gray-800 p-4">
      <div className="flex items-center gap-1.5 text-gray-500 text-xs uppercase tracking-wide mb-1">
        {icon}
        {label}
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  )
}
