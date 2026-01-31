import { useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import { ThemeContext, type Theme } from './ThemeContext'

// Initialize theme synchronously before React renders
function getInitialTheme(): Theme {
  // Use OS preference
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

// Set initial theme on document before React renders
const initialTheme = getInitialTheme()
const root = document.documentElement
if (initialTheme === 'dark') {
  root.classList.add('dark')
} else {
  root.classList.remove('dark')
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(initialTheme)

  useEffect(() => {
    const root = document.documentElement
    // Add/remove 'dark' class for Tailwind dark mode
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [theme])

  const toggleTheme = () => {
    setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

