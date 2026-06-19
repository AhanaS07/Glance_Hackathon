import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'

// Color palette reused across all chart types.
const COLORS = [
  '#3b82f6',
  '#8b5cf6',
  '#ec4899',
  '#f59e0b',
  '#10b981',
  '#06b6d4',
  '#ef4444',
  '#84cc16',
]

// Shared dark-theme styling for axes / tooltip.
const AXIS_STYLE = { fill: '#9ca3af', fontSize: 12 }
const tooltipStyle = {
  backgroundColor: '#1a1a1a',
  border: '1px solid #374151',
  borderRadius: '8px',
  color: '#fff',
}

/**
 * Renders a single chart card based on a chart spec and the raw dataset.
 *
 * @param {Object} chart - { type, title, x, y, insight }
 * @param {Array<Object>} rawData - array of row objects from the dataset
 */
export default function ChartCard({ chart, rawData }) {
  const { type, title, x, y, insight } = chart || {}

  // Build the chart data array by extracting the x/y fields from each row.
  // Coerce y to a number where possible so numeric charts render correctly.
  const chartData = Array.isArray(rawData)
    ? rawData
        .map((row) => {
          if (!row) return null
          const xVal = row[x]
          const yRaw = row[y]
          const yNum = typeof yRaw === 'number' ? yRaw : parseFloat(yRaw)
          return {
            [x]: xVal,
            [y]: Number.isNaN(yNum) ? yRaw : yNum,
          }
        })
        .filter((d) => d && d[x] !== undefined && d[x] !== null)
    : []

  return (
    <div className="bg-card rounded-2xl border border-gray-800 p-5 flex flex-col">
      <h3 className="text-base font-semibold text-white mb-3 truncate">
        {title || 'Chart'}
      </h3>

      {/* Fixed-height responsive chart area */}
      <div className="h-[280px] w-full">
        {!chartData || !chartData.length ? (
          <div className="h-full flex items-center justify-center text-gray-500 text-sm">
            No data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {renderChart(type, chartData, x, y)}
          </ResponsiveContainer>
        )}
      </div>

      {/* Chart insight in a muted color */}
      {insight && <p className="text-sm text-gray-500 mt-3">{insight}</p>}
    </div>
  )
}

// Pick the right Recharts chart based on chart.type.
function renderChart(type, chartData, x, y) {
  switch (type) {
    case 'line':
      return (
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis dataKey={x} tick={AXIS_STYLE} stroke="#374151" />
          <YAxis tick={AXIS_STYLE} stroke="#374151" />
          <Tooltip contentStyle={tooltipStyle} />
          <Line
            type="monotone"
            dataKey={y}
            stroke={COLORS[0]}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      )

    case 'scatter':
      return (
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis dataKey={x} name={x} tick={AXIS_STYLE} stroke="#374151" />
          <YAxis dataKey={y} name={y} tick={AXIS_STYLE} stroke="#374151" />
          <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: '3 3' }} />
          <Scatter data={chartData} fill={COLORS[0]} />
        </ScatterChart>
      )

    case 'pie':
      return (
        <PieChart>
          <Tooltip contentStyle={tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
          <Pie
            data={chartData}
            dataKey={y}
            nameKey={x}
            cx="50%"
            cy="50%"
            outerRadius={80}
            label
          >
            {chartData.map((entry, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      )

    case 'bar':
    default:
      // Default to a bar chart for "bar" and any unknown type.
      return (
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis dataKey={x} tick={AXIS_STYLE} stroke="#374151" />
          <YAxis tick={AXIS_STYLE} stroke="#374151" />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#ffffff0d' }} />
          <Bar dataKey={y} fill={COLORS[0]} radius={[4, 4, 0, 0]} />
        </BarChart>
      )
  }
}
