import { useState, useRef } from 'react'
import './App.css'

import LangList from './LangList.jsx'
import LangChat from './LangChat.jsx'
import { fetchTextStream, fetchJsonStream } from './utils.jsx'

function App() {
  const [article, setArticle] = useState(null)
  const [chunks, setChunks] = useState([])
  const [cursor, setCursor] = useState(-1)
  const [messages, setMessages] = useState([])
  const [translating, setTranslating] = useState(false)
  const [generating, setGenerating] = useState(false)
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
    setTranslating(true)

    try {
      // stream in chunks
      const stream = fetchJsonStream('/api/article', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })

      // add to list
      for await (const chunk of stream) {
        setChunks(cs => [...cs, chunk])
      }
    } catch (err) {
      console.error(err)
      setError(err.message)
    }

    // reset button
    setTranslating(false)
  }

  function getContext() {
    if (cursor >= 0 && cursor < chunks.length) {
      const [orig, trans] = chunks[cursor]
      return { orig, trans }
    }
    return {}
  }

  async function handleGenerate(query) {
    // hide prompt
    setGenerating(true)

    // save user query
    const user = { role: 'user', content: query }
    setMessages(cs => [...cs, user])

    try {
      // stream in chunks
      const stream = fetchTextStream('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, ...getContext() })
      })

      // create new message
      const asst = {role: 'assistant', content: ''}
      setMessages(cs => [...cs, asst])

      // add in content chunks
      for await (const chunk of stream) {
        setMessages(cs => {
          const nhist = cs.length - 1
          const start = cs.slice(0, nhist)
          const { role, content } = cs[nhist]
          const content1 = content + chunk
          return [...start, {role, content: content1}]
        })
      }
    } catch (err) {
      console.error(err)
      setError(err.message)
    }

    // show prompt
    setGenerating(false)
  }

  return (
    <div className="flex flex-row h-screen w-screen">
      <div className="flex flex-col flex-1 h-full">
        <div className="relative flex flex-row border-b border-gray-300">
          <input ref={inputRef} type="text" className="w-full p-2 outline-none font-mono bg-gray-100" placeholder="Enter article url" />
          <div className="absolute right-0 h-full p-2">
            <button className={`px-1 bg-blue-500 text-white h-full w-full rounded-sm font-bold text-sm ${translating ? 'opacity-50' : ''}`} disabled={translating} onClick={handleTranslate}>Translate</button>
          </div>
        </div>
        <div className="flex-1 w-full min-h-0">
          <LangList chunks={chunks} cursor={cursor} setCursor={setCursor} />
        </div>
      </div>
      <div className="w-[450px] h-full border-l border-gray-300 bg-gray-100">
        {article && <LangChat messages={messages} onSubmit={handleGenerate} generating={generating} />}
      </div>
      {error && <div className="absolute bottom-5 right-5 w-[350px] border rounded border-gray-300 bg-gray-100 p-2 overflow-y-auto">
        {error}
      </div>}
    </div>
  )
}

export default App
