import { useMemo } from 'react'
import type { Offer, Product } from './types'
import { useProductBackground } from './hooks/useProductBackground'

type DateInfo = {
  date: Date
  day: number
  month: number
  year: number
  isFirstOfMonth: boolean
}

type DateSpan = {
  startIndex: number
  endIndex: number
  span: number
}

function getDateRange(offers: Offer[]): Date[] {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  let maxDate = today

  // Find the latest end date
  offers.forEach((offer) => {
    if (offer.validity_end_date) {
      const endDate = new Date(offer.validity_end_date)
      endDate.setHours(0, 0, 0, 0)
      if (endDate > maxDate) {
        maxDate = endDate
      }
    }
  })

  // Generate all dates from today to maxDate
  const dates: Date[] = []
  const current = new Date(today)
  while (current <= maxDate) {
    dates.push(new Date(current))
    current.setDate(current.getDate() + 1)
  }

  return dates
}

function isOfferActiveOnDate(offer: Offer, date: Date): boolean {
  if (!offer.validity_start_date || !offer.validity_end_date) {
    return false
  }

  const startDate = new Date(offer.validity_start_date)
  startDate.setHours(0, 0, 0, 0)
  const endDate = new Date(offer.validity_end_date)
  endDate.setHours(0, 0, 0, 0)
  const checkDate = new Date(date)
  checkDate.setHours(0, 0, 0, 0)

  return checkDate >= startDate && checkDate <= endDate
}

function getDateSpansForOffer(
  offer: Offer,
  dates: Date[]
): (DateSpan | null)[] {
  const spans: (DateSpan | null)[] = []
  for (let i = 0; i < dates.length; i++) {
    spans.push(null)
  }
  let currentSpan: DateSpan | null = null

  dates.forEach((date, index) => {
    const isActive = isOfferActiveOnDate(offer, date)

    if (isActive) {
      if (currentSpan === null) {
        // Start a new span
        currentSpan = {
          startIndex: index,
          endIndex: index,
          span: 1,
        }
      } else {
        // Extend current span
        currentSpan.endIndex = index
        currentSpan.span = index - currentSpan.startIndex + 1
      }
      spans[index] = null // Mark as part of a span (will be rendered with grid-column span)
    } else {
      if (currentSpan !== null) {
        // Close the current span
        const spanToStore: DateSpan = currentSpan
        spans[spanToStore.startIndex] = spanToStore
        currentSpan = null
      }
      spans[index] = null // Inactive date, empty cell
    }
  })

  // Close any remaining span
  if (currentSpan !== null) {
    const spanToStore: DateSpan = currentSpan
    spans[spanToStore.startIndex] = spanToStore
  }

  return spans
}

export function ProductTimetable({ product }: { product: Product }) {
  const allOffers = useMemo(() => {
    return product.extracted_data
      .filter((item) => item.offers && item.offers.length > 0)
      .flatMap((item) => item.offers!)
  }, [product.extracted_data])

  const dates = useMemo(() => getDateRange(allOffers), [allOffers])

  const dateInfos = useMemo(() => {
    return dates.map((date, index) => {
      const prevDate = index > 0 ? dates[index - 1] : null
      const isFirstOfMonth =
        !prevDate || date.getMonth() !== prevDate.getMonth()

      return {
        date,
        day: date.getDate(),
        month: date.getMonth(),
        year: date.getFullYear(),
        isFirstOfMonth,
      } as DateInfo
    })
  }, [dates])

  const productName = product.extracted_data[0]?.product_name || product.slug
  const productThumbnailUrl = product.extracted_data[0]?.product_thumbnail_url
  const productBackgroundStyle = useProductBackground(productThumbnailUrl)

  // Grid template: 1 column for retailer (120px) + N columns for dates (50px each)
  const gridTemplateColumns = `120px repeat(${dates.length}, 43px)`

  return (
    <div className="bg-gray-100 dark:bg-white/5 border border-gray-300 dark:border-white/10 rounded-xl p-1 transition-transform hover:translate-y-[-4px] hover:shadow-lg">
      {allOffers.length === 0 ? (
        <div className="text-gray-600 dark:text-gray-400">No offers available</div>
      ) : (
        <div className="overflow-x-auto">
          <div
            className="inline-block min-w-full"
            role="table"
            aria-label="Product price timeline"
          >
            {/* Header row */}
            <div
              className="grid border-b-2 border-gray-300 dark:border-gray-700"
              style={{ gridTemplateColumns }}
            >
              <div
                className="sticky left-0 z-20 bg-white dark:bg-gray-900 border-r-2 border-gray-300 dark:border-gray-700 px-4 py-2 text-left relative"
                role="columnheader"
                style={productBackgroundStyle}
              >
                {productThumbnailUrl && (
                  <div className="absolute inset-0 bg-white/70 dark:bg-gray-900/70" />
                )}
                <div className="flex flex-wrap items-center gap-1 relative z-10">
                  <h2 className="text-lg font-semibold capitalize text-blue-600 dark:text-blue-400">
                    {productName}
                  </h2>
                  <span className="text-gray-600 dark:text-gray-400 text-sm">
                    (
                    <a
                      href={product.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      →
                    </a>)
                  </span>
                </div>
              </div>
              {dateInfos.map((dateInfo, idx) => {
                const dayOfWeek = dateInfo.date.getDay()
                const isWeekend = dayOfWeek === 0 || dayOfWeek === 6 // Sunday or Saturday
                return (
                  <div
                    key={idx}
                    className={`border-l border-r border-gray-300 dark:border-gray-700 px-2 py-2 text-center ${
                      isWeekend 
                        ? 'bg-gray-200/70 dark:bg-gray-700/70' 
                        : 'bg-gray-100/50 dark:bg-gray-800/50'
                    }`}
                    role="columnheader"
                  >
                    <div className="flex flex-row items-center justify-center gap-1">
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                        {dateInfo.day}
                      </span>
                      {dateInfo.isFirstOfMonth && (
                        <span className="text-xs text-gray-600 dark:text-gray-400">
                          .{dateInfo.month + 1}.
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Data rows */}
            {allOffers.map((offer, offerIdx) => {
              const dateSpans: (DateSpan | null)[] =
                getDateSpansForOffer(offer, dates)

              return (
                <div
                  key={offerIdx}
                  className="grid border-b border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5"
                  style={{ gridTemplateColumns }}
                  role="row"
                >
                  {/* Retailer cell */}
                  <div
                    className="sticky left-0 z-10 bg-white dark:bg-gray-900 border-r-2 border-gray-300 dark:border-gray-700 flex items-center px-2"
                    role="gridcell"
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      {offer.retailer_logo && (
                        <img
                          src={offer.retailer_logo}
                          alt={offer.retailer_name}
                          className="w-8 h-8 object-contain rounded bg-gray-200 dark:bg-white/10 p-1 flex-shrink-0"
                        />
                      )}
                      <span className="font-semibold text-gray-800 dark:text-gray-200 truncate">
                        {offer.retailer_name}
                      </span>
                    </div>
                  </div>

                  {/* Date cells */}
                  {dateInfos.map((dateInfo, dateIdx) => {
                    const span = dateSpans[dateIdx]
                    const isActive = isOfferActiveOnDate(offer, dateInfo.date)
                    const dayOfWeek = dateInfo.date.getDay()
                    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6 // Sunday or Saturday

                    // Skip rendering if this is part of a span (not the start)
                    if (span === null && isActive) {
                      return null
                    }

                    // Render merged cell at the start of a span
                    if (span !== null && span.startIndex === dateIdx) {
                      return (
                        <div
                          key={dateIdx}
                          className={`border-l border-r border-gray-300 dark:border-gray-700 text-center transition-colors flex items-center justify-center ${
                            isWeekend
                              ? 'bg-gradient-to-r from-green-400/40 via-green-400/35 to-green-400/40 dark:from-green-500/30 dark:via-green-500/25 dark:to-green-500/30 hover:from-green-400/50 hover:via-green-400/45 hover:to-green-400/50 dark:hover:from-green-500/40 dark:hover:via-green-500/35 dark:hover:to-green-500/40'
                              : 'bg-gradient-to-r from-green-400/35 via-green-400/30 to-green-400/35 dark:from-green-500/25 dark:via-green-500/20 dark:to-green-500/25 hover:from-green-400/45 hover:via-green-400/40 hover:to-green-400/45 dark:hover:from-green-500/35 dark:hover:via-green-500/30 dark:hover:to-green-500/35'
                          }`}
                          style={{ gridColumn: `span ${span.span}` }}
                          role="gridcell"
                        >
                          <div className="flex flex-row flex-wrap items-center justify-center gap-2">
                            {offer.retailer_logo && (
                              <img
                                src={offer.retailer_logo}
                                alt={offer.retailer_name}
                                className="w-8 h-8 object-contain rounded bg-gray-200 dark:bg-white/20 p-1"
                              />
                            )}
                            <span className="text-sm font-semibold text-green-700 dark:text-green-300">
                              {offer.price}
                            </span>
                            {offer.discount && (
                              <span className="text-xs bg-red-500 text-white px-2 py-1 rounded font-semibold">
                                {offer.discount}
                              </span>
                            )}
                          </div>
                        </div>
                      )
                    }

                    // Render empty cell for inactive dates
                    return (
                      <div
                        key={dateIdx}
                        className={`border-l border-r border-gray-300 dark:border-gray-700 flex items-center ${
                          isWeekend ? 'bg-gray-200/50 dark:bg-gray-700/50' : 'bg-gray-100/30 dark:bg-gray-800/30'
                        }`}
                        role="gridcell"
                      >
                      </div>
                    )
                  })}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

