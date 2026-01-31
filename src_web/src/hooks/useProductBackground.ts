import { useMemo } from 'react'
import type { CSSProperties } from 'react'

export function useProductBackground(thumbnailUrl: string | null | undefined) {
  return useMemo(() => {
    if (!thumbnailUrl) {
      return {}
    }

    return {
      backgroundImage: `url(${thumbnailUrl})`,
      backgroundSize: '60% auto',
      backgroundPosition: 'right center',
      backgroundRepeat: 'repeat',
    } as CSSProperties
  }, [thumbnailUrl])
}

