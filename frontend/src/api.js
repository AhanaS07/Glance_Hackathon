// API client for the CSV Insights Dashboard.
// Connects directly to the FastAPI backend running on localhost:8000.

const API_BASE_URL = 'http://localhost:8000'

/**
 * Upload a CSV file to the backend for analysis.
 *
 * @param {File} file - A CSV File object selected by the user.
 * @returns {Promise<Object>} The parsed JSON analysis response.
 * @throws {Error} If the request fails or the API returns an error.
 */
export async function analyzeCSV(file) {
  // Build multipart form data with the file under the field name "file".
  const formData = new FormData()
  formData.append('file', file)

  let response
  try {
    response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    // fetch only rejects on network-level failures (server down, CORS, etc.)
    throw new Error(
      'Could not reach the server. Make sure the backend is running on localhost:8000.',
    )
  }

  // Try to parse JSON regardless of status so we can surface server error messages.
  let payload
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    // Prefer a meaningful message from the API (FastAPI commonly uses "detail").
    const message =
      (payload && (payload.detail || payload.error || payload.message)) ||
      `Analysis failed with status ${response.status}.`
    throw new Error(message)
  }

  if (!payload) {
    throw new Error('Received an empty or invalid response from the server.')
  }

  return payload
}
