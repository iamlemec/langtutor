// utilities

function lineStreamer(chunk, controller) {
    const lines = chunk.split('\n')
    for (const line of lines) {
        if (line.length > 0) {
            const data = JSON.parse(line)
            controller.enqueue(data)
        }
    }
}

async function* fetchStream(url, args={}) {
    // connect and get status
    const response = await fetch(url, args)
    if (!response.ok) {
        throw new Error(`HTTP error: status ${response.status}`)
    }

    // make reader and decode
    const reader = response.body
        .pipeThrough(new TextDecoderStream())
        .pipeThrough(new TransformStream({ transform: lineStreamer }))

    // yield stream of chunks
    for await (const chunk of reader) {
        yield chunk
    }
}

export { fetchStream }
