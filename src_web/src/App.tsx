import { useState, useEffect } from 'react'
import { ProductTimetable } from './ProductTimetable'
import { ThemeToggle } from './components/ThemeToggle'
import type { Product } from './types'

function App() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/combined_data.json')
      .then((res) => {
        if (!res.ok) {
          throw new Error('Failed to load data')
        }
        return res.json()
      })
      .then((data: Product[]) => {
        setProducts(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white transition-colors">
        <div className="max-w-[1400px] mx-auto p-8">
          <div className="text-center py-8 text-xl">Loading products...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white transition-colors">
        <div className="max-w-[1400px] mx-auto p-8">
          <div className="text-center py-8 text-xl text-red-500 dark:text-red-400">
            Error: {error}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white transition-colors">
      <ThemeToggle />
      <div className="max-w-[1400px] mx-auto p-8">
        <h1 className="text-center text-4xl font-bold mb-8">Price Timeline</h1>
        <div className="grid grid-cols-1 gap-8">
          {products.map((product) => (
            <ProductTimetable key={product.slug} product={product} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default App
