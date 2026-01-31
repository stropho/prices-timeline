export type Offer = {
  retailer_name: string
  retailer_logo: string | null
  price: string
  discount: string | null
  validity: string
  validity_start_date: string | null
  validity_end_date: string | null
}

export type ExtractedData = {
  index: number
  product_name?: string
  product_thumbnail_url?: string | null
  product_category?: string | null
  offers?: Offer[]
  tags?: string[]
  content?: string[]
  error: boolean
}

export type Product = {
  slug: string
  url: string
  markdown: string
  extracted_data: ExtractedData[]
}

