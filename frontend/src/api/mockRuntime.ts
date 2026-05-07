import type { AxiosError } from 'axios'

const MOCK_DELAY_MS = 180

interface MockFallbackOptions {
  shouldFallback?: (error: unknown) => boolean
}

export function shouldUseMock(): boolean {
  return import.meta.env.DEV && import.meta.env.VITE_USE_MOCK === 'true'
}

export async function withMockFallback<T>(
  request: () => Promise<T>,
  fallback: () => Promise<T> | T,
  options: MockFallbackOptions = {},
): Promise<T> {
  try {
    return await request()
  } catch (error) {
    if (!shouldUseMock() || !isFallbackAllowed(error, options.shouldFallback)) {
      throw error
    }

    await sleep(MOCK_DELAY_MS)
    return fallback()
  }
}

function isFallbackAllowed(
  error: unknown,
  customRule?: (error: unknown) => boolean,
): boolean {
  if (customRule) {
    return customRule(error)
  }

  const axiosError = error as AxiosError | undefined
  if (!axiosError?.isAxiosError) {
    return true
  }

  const statusCode = axiosError.response?.status
  if (typeof statusCode !== 'number') {
    return true
  }

  return statusCode >= 500 || statusCode === 404 || statusCode === 405
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}
