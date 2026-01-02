import { ref } from 'vue'

/**
 * API composable for making HTTP requests
 */
export function useApi() {
  const loading = ref(false)
  const error = ref(null)

  const get = async (path) => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(path)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      return await response.json()
    } catch (e) {
      error.value = e.message
      console.error(`GET ${path} failed:`, e)
      return null
    } finally {
      loading.value = false
    }
  }

  const post = async (path, data) => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(path, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })

      const result = await response.json()

      if (!response.ok) {
        error.value = result.error || `HTTP ${response.status}`
      }

      return result
    } catch (e) {
      error.value = e.message
      console.error(`POST ${path} failed:`, e)
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    get,
    post
  }
}
