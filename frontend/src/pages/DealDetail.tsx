import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  ExternalLink,
  Loader2,
  Cpu,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { format } from 'date-fns'
import { fetchDeal, analyzeDeal, fetchPriceHistory } from '../api'
import { DealScoreBadge } from '../components/DealScoreBadge'
import { RecommendationBadge } from '../components/RecommendationBadge'

export function DealDetail() {
  const { id } = useParams<{ id: string }>()
  const dealId = parseInt(id ?? '0', 10)
  const queryClient = useQueryClient()

  const { data: deal, isLoading } = useQuery({
    queryKey: ['deal', dealId],
    queryFn: () => fetchDeal(dealId),
    enabled: !!dealId,
  })

  const { data: priceHistory } = useQuery({
    queryKey: ['price-history', deal?.listing_id],
    queryFn: () => fetchPriceHistory(deal!.listing_id),
    enabled: !!deal?.listing_id,
  })

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeDeal(dealId),
    onSuccess: (updatedDeal) => {
      queryClient.setQueryData(['deal', dealId], updatedDeal)
    },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
      </div>
    )
  }

  if (!deal) {
    return (
      <div className="p-6">
        <p className="text-red-400">Deal not found.</p>
        <Link to="/deals" className="text-blue-400 hover:text-blue-300 text-sm mt-2 inline-block">
          ← Back to Deals
        </Link>
      </div>
    )
  }

  const listing = deal.listing
  const chartData = priceHistory?.map((ph) => ({
    date: format(new Date(ph.recorded_at), 'MMM d'),
    price: ph.price,
  }))

  const savings =
    deal.price_difference != null && deal.price_difference > 0
      ? deal.price_difference
      : null

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/deals" className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold text-white truncate">
            {listing?.title ?? `Deal #${deal.id}`}
          </h1>
          <p className="text-sm text-gray-400 mt-0.5 capitalize">
            {listing?.source ?? '?'} ·{' '}
            {listing?.brand ?? ''}{listing?.model ? ` ${listing.model}` : ''}
          </p>
        </div>
        {listing?.url && (
          <a
            href={listing.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            View Listing
          </a>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main info */}
        <div className="lg:col-span-2 space-y-4">
          {/* Price comparison */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Price Analysis
            </h2>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-gray-500">Listing Price</p>
                <p className="text-2xl font-bold text-white mt-1">
                  €{listing?.price?.toLocaleString() ?? '?'}
                </p>
              </div>
              {deal.market_price && (
                <div>
                  <p className="text-xs text-gray-500">Market Avg</p>
                  <p className="text-2xl font-bold text-gray-300 mt-1">
                    €{deal.market_price.toLocaleString()}
                  </p>
                </div>
              )}
              {deal.price_difference_pct != null && (
                <div>
                  <p className="text-xs text-gray-500">Difference</p>
                  <p
                    className={`text-2xl font-bold mt-1 flex items-center gap-1 ${
                      deal.price_difference_pct > 0 ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {deal.price_difference_pct > 0 ? (
                      <TrendingDown className="w-5 h-5" />
                    ) : (
                      <TrendingUp className="w-5 h-5" />
                    )}
                    {Math.abs(deal.price_difference_pct).toFixed(1)}%
                  </p>
                  {savings && (
                    <p className="text-xs text-green-500 mt-0.5">Save €{savings.toLocaleString()}</p>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Listing details */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Listing Details
            </h2>
            <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
              {[
                ['Brand', listing?.brand],
                ['Model', listing?.model],
                ['Reference', listing?.reference_number],
                ['Condition', listing?.condition],
                ['Year', listing?.year],
                ['Location', listing?.location],
                ['Seller', listing?.seller_name],
                ['Currency', listing?.currency],
              ].map(([label, value]) =>
                value ? (
                  <div key={label as string}>
                    <span className="text-gray-500">{label}:</span>{' '}
                    <span className="text-gray-200">{value}</span>
                  </div>
                ) : null
              )}
            </div>
            {listing?.description && (
              <div className="mt-4 pt-4 border-t border-gray-800">
                <p className="text-xs text-gray-500 mb-2">Description</p>
                <p className="text-sm text-gray-300 whitespace-pre-line line-clamp-5">
                  {listing.description}
                </p>
              </div>
            )}
            {listing?.image_urls && listing.image_urls.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-800">
                <p className="text-xs text-gray-500 mb-2">Images</p>
                <div className="flex gap-2 flex-wrap">
                  {listing.image_urls.slice(0, 4).map((url, i) => (
                    <img
                      key={i}
                      src={url}
                      alt={`Watch ${i + 1}`}
                      className="w-20 h-20 object-cover rounded-lg border border-gray-700"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Price history chart */}
          {chartData && chartData.length > 1 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                Price History
              </h2>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" tick={{ fill: '#9ca3af', fontSize: 11 }} tickLine={false} />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#f9fafb',
                    }}
                    formatter={(v: number) => [`€${v.toLocaleString()}`, 'Price']}
                  />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={{ fill: '#8b5cf6', r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Sidebar: score + AI */}
        <div className="space-y-4">
          {/* Deal score */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Deal Score
            </h2>
            <div className="flex items-center gap-3 mb-3">
              <DealScoreBadge score={deal.deal_score} size="lg" />
              {deal.ai_recommendation && (
                <RecommendationBadge recommendation={deal.ai_recommendation} size="sm" />
              )}
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  deal.deal_score >= 0.8
                    ? 'bg-green-500'
                    : deal.deal_score >= 0.6
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                }`}
                style={{ width: `${deal.deal_score * 100}%` }}
              />
            </div>
          </div>

          {/* AI Analysis */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                AI Analysis
              </h2>
              <button
                onClick={() => analyzeMutation.mutate()}
                disabled={analyzeMutation.isPending}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-xs font-medium text-white transition-colors"
              >
                {analyzeMutation.isPending ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Cpu className="w-3 h-3" />
                )}
                Analyze
              </button>
            </div>

            {deal.ai_analysis ? (
              <p className="text-sm text-gray-300 leading-relaxed">{deal.ai_analysis}</p>
            ) : (
              <p className="text-sm text-gray-500 italic">
                No AI analysis yet. Click Analyze to get Claude's assessment.
              </p>
            )}

            {analyzeMutation.isError && (
              <p className="mt-2 text-xs text-red-400">
                Analysis failed. Check your ANTHROPIC_API_KEY.
              </p>
            )}
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-500 space-y-1">
            <p>Deal ID: #{deal.id}</p>
            <p>Listed: {format(new Date(deal.created_at), 'MMM d, yyyy HH:mm')}</p>
            <p>Notified: {deal.is_notified ? 'Yes' : 'No'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
