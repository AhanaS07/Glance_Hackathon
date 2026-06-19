import { Lightbulb } from 'lucide-react'

// Displays a single AI-generated insight string.
export default function InsightCard({ text }) {
  return (
    <div className="bg-card rounded-2xl border border-gray-800 p-5 flex items-start gap-3 hover:border-gray-700 transition-colors">
      <div className="p-2 rounded-lg bg-amber-400/10 shrink-0">
        <Lightbulb className="w-5 h-5 text-amber-400" />
      </div>
      <p className="text-gray-300 leading-relaxed text-sm">{text}</p>
    </div>
  )
}
