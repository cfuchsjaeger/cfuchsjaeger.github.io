import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ExternalLink, Loader2 } from 'lucide-react'
import { fetchListings } from '../api'

export function Listings() {
  const [source, setSource] = useState('')
  const [brand, setBrand] = useState('')
  const [isActive, setIsActive] = useState<string>('true')

  const { data: listings, isLoading, error } = useQuery({
    queryKey: ['listings', { source, brand, isActive }],
    queryFn: () =>
      fetchListings({
        source: source || undefined,
        brand: brand || undefined,
        is_active: isActive === '' ? undefined : isActive === 'true',
        limit: 100,
      }),
  })

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Listings</h1>
        <p className="text-sm text-gray-400 mt-0.5">All scraped watch listings</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Source</label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="w-36 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">All Sources</option>
            <option value="willhaben">Willhaben</option>
            <option value="chrono24">Chrono24</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Brand</label>
          <input
            type="text"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            placeholder="e.g. Rolex"
            className="w-36 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Status</label>
          <select
            value={isActive}
            onChange={(e) => setIsActive(e.target.value)}
            className="w-28 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
        </div>
      ) : error ? (
        <div className="bg-red-900/30 border border-red-700/50 rounded-lg px-4 py-3 text-sm text-red-300">
          Failed to load listings. Is the backend running?
        </div>
      ) : listings && listings.length > 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-left">
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Title</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Brand</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Price</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Condition</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Source</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Location</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {listings.map((listing) => (
                  <tr key={listing.id} className="hover:bg-gray-800/50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-white line-clamp-2 max-w-xs">{listing.title}</p>
                      {listing.reference_number && (
                        <p className="text-xs text-gray-500 mt-0.5">Ref: {listing.reference_number}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-300">{listing.brand || <span className="text-gray-600">—</span>}</td>
                    <td className="px-4 py-3 text-white font-medium">
                      €{listing.price.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-gray-300 text-xs">{listing.condition || <span className="text-gray-600">—</span>}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                          listing.source === 'willhaben'
                            ? 'bg-orange-500/20 text-orange-300'
                            : 'bg-purple-500/20 text-purple-300'
                        }`}
                      >
                        {listing.source}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{listing.location || <span className="text-gray-600">—</span>}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                          listing.is_active
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-gray-500/20 text-gray-400'
                        }`}
                      >
                        {listing.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={listing.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-500 hover:text-gray-300"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <p className="text-gray-400">No listings found. Run a scrape from the Dashboard.</p>
        </div>
      )}
    </div>
  )
}
