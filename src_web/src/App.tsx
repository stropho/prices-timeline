import { ProductTimetable } from './ProductTimetable'
import { ThemeToggle } from './components/ThemeToggle'
import type { Product } from './types'

const productModules = import.meta.glob<{ default: Product }>('./json/*.json', {
  eager: true,
})

const products = Object.values(productModules)
  .map((module) => module.default)
  .sort((a, b) => a.slug.localeCompare(b.slug))

function App() {

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white transition-colors">
      <ThemeToggle />
      <div className="max-w-[1400px] mx-auto 1">
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
