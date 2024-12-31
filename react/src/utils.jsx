// utilities

async function* fetchStream(url, args={}) {
    try {
        // connect and get status
        const response = await fetch(url, args)
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        // make reader and decoder
        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')

        // yield stream of chunks
        while (true) {
            const { done, value } = await reader.read()
            if (done) break
            const result = decoder.decode(value, { stream: true })
            yield result
        }
    } catch (error) {
        console.error('Error fetching stream:', error)
    }
}

export { fetchStream }
