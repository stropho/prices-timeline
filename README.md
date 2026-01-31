# Prices Timeline

A full-stack application for tracking and visualizing promotional product deals. Consists of a Python web crawler that extracts deal data and a React-based front-end application that displays price timelines.

## Features

### Crawler
- Crawls specific product pages
- Extracts promotional offers with pricing, retailers, validity dates
- Handles JavaScript-rendered content using Playwright
- Saves raw and processed data to JSON files
- Always fetches fresh data (no caching)

### Web Application
- Interactive price timeline visualization
- Dark mode support
- Responsive design
- Built with React, TypeScript, and Tailwind CSS

## Setup

### Crawler Setup

1. **Install dependencies:**
   ```bash
   cd src_crawler
   uv sync
   ```

2. **Configure URLs:**
   Edit `src_crawler/config/urls.txt` and add target URLs (one per line)

3. **Optional: Create .env file:**
   ```bash
   cp .env.example .env
   ```

### Web Application Setup

1. **Install dependencies:**
   ```bash
   cd src_web
   npm install
   ```

2. **Run development server:**
   ```bash
   npm run dev
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

4. **Preview production build:**
   ```bash
   npm run preview
   ```

## Type Checking

This project uses comprehensive type hints (similar to TypeScript) for better code safety and IDE support.

**Run type checking:**
```bash
cd src_crawler && uv run mypy .
```

## Usage

### Running the Crawler

**Run the crawler:**
```bash
cd src_crawler && uv run main.py
```

### Running the Web Application

**Development mode:**
```bash
cd src_web && npm run dev
```

The application will be available at `http://localhost:5173` (or the port shown in the terminal).

**Production build:**
```bash
cd src_web && npm run build
```

The built files will be in `src_web/dist/`.

## Deployment

The web application is automatically deployed to GitHub Pages when:
- Changes are pushed to the `main` branch
- Files in `src_web/` are modified

The deployment workflow is defined in `.github/workflows/deploy-pages.yaml`.


## Project Structure

```
prices-timeline/
├── src_crawler/        # Python crawler project
│   ├── crawlers/       # Crawler implementations
│   ├── extractors/     # Extraction schemas
│   ├── config/         # Configuration files
│   │   └── urls.txt   # Target URLs to crawl
│   ├── utils/         # Helper utilities
│   ├── main.py        # Entry point
│   ├── models.py      # Data models
│   ├── pyproject.toml # Project configuration
│   └── requirements.txt # Python dependencies
├── src_web/           # React web application
│   ├── src/           # Source code
│   │   ├── components/ # React components
│   │   ├── hooks/      # Custom React hooks
│   │   └── ...
│   ├── public/        # Static assets
│   │   └── combined_data.json # Product data
│   ├── package.json   # Node.js dependencies
│   └── vite.config.ts # Vite configuration
├── .github/
│   └── workflows/     # GitHub Actions workflows
│       └── deploy-pages.yaml # GitHub Pages deployment
├── data/
│   ├── raw/           # Raw crawl results
│   └── processed/     # Processed JSON files
└── README.md          # This file
```

## Output

- **Raw data:** `data/raw/{product_slug}_{timestamp}.json`
- **Processed data:** `data/processed/{product_slug}_latest.json`

## Data Structure

Extracted data includes:
- Product name and category
- Regular price
- Promotional offers:
  - Retailer name and links
  - Promotional price and discount percentage
  - Validity dates (start/end)
  - Flyer and store location URLs
  - Store count

