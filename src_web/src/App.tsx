import { ProductTimetable } from './ProductTimetable'
import { ThemeToggle } from './components/ThemeToggle'
import type { Product } from './types'

const productModules = import.meta.glob<{ default: Product }>('./json/*.json', {
  eager: true,
})

const products = Object.values(productModules)
  .map((module) => module.default)
  .sort(
    (a, b) =>
      (a.commonProductName ?? a.slug).localeCompare(b.commonProductName ?? b.slug) ||
      a.slug.localeCompare(b.slug)
  )

// Consecutive products sharing a commonProductName are rendered together with a small gap
const productGroups = products.reduce<Product[][]>((groups, product) => {
  const last = groups[groups.length - 1]
  if (last && product.commonProductName && last[0].commonProductName === product.commonProductName) {
    last.push(product)
  } else {
    groups.push([product])
  }
  return groups
}, [])

function App() {

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white transition-colors">
      <ThemeToggle />
      <div className="max-w-[1400px] mx-auto 1">
        <div className="grid grid-cols-1 gap-8">
          {productGroups.map((group) => (
            <div key={group[0].slug} className="grid grid-cols-1 gap-1">
              {group.map((product, index) => (
                <ProductTimetable
                  key={product.slug}
                  product={product}
                  compact={index > 0}
                  flushBottom={index < group.length - 1}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default App
