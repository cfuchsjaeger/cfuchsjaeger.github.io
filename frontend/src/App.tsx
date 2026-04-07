import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Deals } from './pages/Deals'
import { DealDetail } from './pages/DealDetail'
import { Listings } from './pages/Listings'
import { SearchConfigs } from './pages/SearchConfigs'
import { ListingCreator } from './pages/ListingCreator'

export default function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/deals" element={<Deals />} />
          <Route path="/deals/:id" element={<DealDetail />} />
          <Route path="/listings" element={<Listings />} />
          <Route path="/search-configs" element={<SearchConfigs />} />
          <Route path="/listing-creator" element={<ListingCreator />} />
        </Route>
      </Routes>
    </Router>
  )
}
