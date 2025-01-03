// utilities

function jsonlParser(chunk, controller) {
    const lines = chunk.split('\n')
    for (const line of lines) {
        if (line.length > 0) {
            const data = JSON.parse(line)
            controller.enqueue(data)
        }
    }
}

async function* fetchStream(url, transform=null, args={}) {
    // connect and get status
    const response = await fetch(url, args)
    if (!response.ok) {
        throw new Error(`HTTP error: status ${response.status}`)
    }

    // make reader and decode
    const reader = response.body.pipeThrough(new TextDecoderStream())
    const stream = transform ? reader.pipeThrough(new TransformStream({ transform })) : reader

    // yield stream of chunks
    for await (const chunk of stream) {
        yield chunk
    }
}

async function* fetchTextStream(url, args={}) {
    yield* fetchStream(url, null, args)
}

async function* fetchJsonStream(url, args={}) {
    yield* fetchStream(url, jsonlParser, args)
}

export { fetchStream, fetchTextStream, fetchJsonStream }
