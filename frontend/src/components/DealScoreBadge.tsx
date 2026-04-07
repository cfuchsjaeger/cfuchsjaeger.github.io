import clsx from 'clsx'

interface DealScoreBadgeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
}

export function DealScoreBadge({ score, size = 'md' }: DealScoreBadgeProps) {
  const pct = Math.round(score * 100)

  const colorClass =
    score >= 0.8
      ? 'bg-green-500/20 text-green-400 border-green-500/30'
      : score >= 0.6
        ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
        : 'bg-red-500/20 text-red-400 border-red-500/30'

  const sizeClass =
    size === 'sm'
      ? 'px-1.5 py-0.5 text-xs'
      : size === 'lg'
        ? 'px-3 py-1.5 text-base font-bold'
        : 'px-2 py-1 text-sm font-semibold'

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border font-medium',
        colorClass,
        sizeClass
      )}
    >
      {pct}%
    </span>
  )
}
