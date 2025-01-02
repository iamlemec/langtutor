import { useState, useEffect, useRef } from 'react'
import './App.css'

import LangList from './LangList.jsx'
import LangChat from './LangChat.jsx'
import { fetchStream } from './utils.jsx'

const init_chunks = [
  ['Hello world', 'Hello world'],
  ['This is a test', 'This is a test'],
]

const init_messages = [
  {role: 'user', content: 'Hello world'},
  {role: 'assistant', content: 'This is a test'},
]

function App() {
  const [article, setArticle] = useState(null)
  const [chunks, setChunks] = useState(init_chunks)
  const [cursor, setCursor] = useState(-1)
  const [messages, setMessages] = useState(init_messages)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  async function handleTranslate() {
    // get article url
    const url = inputRef.current.value
    if (url.length == 0) return

    // reset ui
    setArticle(url)
    setMessages([])
    setChunks([])
    setCursor(-1)

    // stream in chunks
    try {
      const stream = fetchStream('/api/article', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })

      // add to list
      for await (const chunk of stream) {
        setChunks(cs => [...cs, chunk])
      }
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="flex flex-row h-screen w-screen">
      <div className="flex flex-col flex-1 h-full">
        <div className="relative flex flex-row border-b border-gray-200">
          <input type="text" className="w-full p-2 outline-none font-mono bg-gray-100" ref={inputRef} />
          <div className="absolute right-0 h-full p-2">
            <button className="px-1 bg-blue-500 text-white h-full w-full rounded font-bold text-sm" onClick={handleTranslate}>Translate</button>
          </div>
        </div>
        <div className="flex-1 w-full">
          <LangList chunks={chunks} cursor={cursor} setCursor={setCursor} />
        </div>
      </div>
      <div className="w-[400px] h-full border-l border-gray-200">
        <LangChat messages={messages} />
      </div>
      {error && <div className="absolute bottom-5 right-5 w-[350px] border rounded border-gray-300 bg-gray-100 p-2 overflow-y-auto">
        {error}
      </div>}
    </div>
  )
}

export default App
