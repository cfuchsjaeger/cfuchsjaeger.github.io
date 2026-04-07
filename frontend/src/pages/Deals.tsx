import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Loader2, ExternalLink, TrendingDown } from 'lucide-react'
import { fetchDeals } from '../api'
import { DealScoreBadge } from '../components/DealScoreBadge'
import { RecommendationBadge } from '../components/RecommendationBadge'

export function Deals() {
  const [minScore, setMinScore] = useState('')
  const [recommendation, setRecommendation] = useState('')

  const { data: deals, isLoading, error } = useQuery({
    queryKey: ['deals', { minScore, recommendation }],
    queryFn: () =>
      fetchDeals({
        min_score: minScore ? parseFloat(minScore) / 100 : undefined,
        recommendation: recommendation || undefined,
        limit: 100,
      }),
  })

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Deals</h1>
        <p className="text-sm text-gray-400 mt-0.5">Scored watch deals from all sources</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Min Score (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            value={minScore}
            onChange={(e) => setMinScore(e.target.value)}
            placeholder="e.g. 60"
            className="w-28 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Recommendation</label>
          <select
            value={recommendation}
            onChange={(e) => setRecommendation(e.target.value)}
            className="w-32 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">All</option>
            <option value="buy">Buy</option>
            <option value="watch">Watch</option>
            <option value="skip">Skip</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
        </div>
      ) : error ? (
        <div className="bg-red-900/30 border border-red-700/50 rounded-lg px-4 py-3 text-sm text-red-300">
          Failed to load deals. Is the backend running?
        </div>
      ) : deals && deals.length > 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-left">
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Watch
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Market
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Savings
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">
                    AI
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {deals.map((deal) => (
                  <tr key={deal.id} className="hover:bg-gray-800/50 transition-colors">
                    <td className="px-4 py-3">
                      <Link
                        to={`/deals/${deal.id}`}
                        className="font-medium text-white hover:text-blue-400 transition-colors line-clamp-2 max-w-xs"
                      >
                        {deal.listing?.title ?? `Deal #${deal.id}`}
                      </Link>
                      {deal.listing?.brand && (
                        <p className="text-xs text-gray-400 mt-0.5">{deal.listing.brand}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-white font-medium">
                      €{deal.listing?.price?.toLocaleString() ?? '?'}
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      {deal.market_price
                        ? `€${deal.market_price.toLocaleString()}`
                        : <span className="text-gray-600">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      {deal.price_difference_pct != null ? (
                        <span
                          className={
                            deal.price_difference_pct > 0
                              ? 'text-green-400 flex items-center gap-1'
                              : 'text-red-400 flex items-center gap-1'
                          }
                        >
                          {deal.price_difference_pct > 0 && (
                            <TrendingDown className="w-3.5 h-3.5" />
                          )}
                          {Math.abs(deal.price_difference_pct).toFixed(1)}%
                          {deal.price_difference_pct > 0 ? ' below' : ' above'}
                        </span>
                      ) : (
                        <span className="text-gray-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <DealScoreBadge score={deal.deal_score} size="sm" />
                    </td>
                    <td className="px-4 py-3">
                      <RecommendationBadge recommendation={deal.ai_recommendation} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-gray-400 capitalize text-xs">
                      {deal.listing?.source ?? '?'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/deals/${deal.id}`}
                          className="text-blue-400 hover:text-blue-300 text-xs font-medium"
                        >
                          View
                        </Link>
                        {deal.listing?.url && (
                          <a
                            href={deal.listing.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-gray-500 hover:text-gray-300"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <p className="text-gray-400">No deals found. Try adjusting the filters or running a scrape.</p>
        </div>
      )}
    </div>
  )
}
