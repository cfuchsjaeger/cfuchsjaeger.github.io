import clsx from 'clsx'
import type { Recommendation } from '../types'

interface RecommendationBadgeProps {
  recommendation: Recommendation | string | null | undefined
  size?: 'sm' | 'md'
}

const CONFIG: Record<string, { label: string; classes: string }> = {
  buy: {
    label: 'BUY',
    classes: 'bg-green-500/20 text-green-300 border-green-500/40',
  },
  watch: {
    label: 'WATCH',
    classes: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
  },
  skip: {
    label: 'SKIP',
    classes: 'bg-red-500/20 text-red-300 border-red-500/40',
  },
}

export function RecommendationBadge({ recommendation, size = 'md' }: RecommendationBadgeProps) {
  if (!recommendation) return null

  const config = CONFIG[recommendation] ?? {
    label: recommendation.toUpperCase(),
    classes: 'bg-gray-500/20 text-gray-300 border-gray-500/40',
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded border font-semibold tracking-wide',
        size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-1 text-xs',
        config.classes
      )}
    >
      {config.label}
    </span>
  )
}
