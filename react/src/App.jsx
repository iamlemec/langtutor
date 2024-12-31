import { useState, useEffect, useRef } from 'react'
import './App.css'

import { fetchStream } from './utils.jsx'

const init = [
  ['Hello world', 'Hello world'],
  ['This is a test', 'This is a test'],
]

function App() {
  const [article, setArticle] = useState(null)
  const [chunks, setChunks] = useState(init)
  const [cursor, setCursor] = useState(-1)
  const inputRef = useRef(null)

  function handleTranslate() {
    // get article url
    const url = inputRef.current.value
    if (url.length == 0) return

    // reset ui
    setArticle(url)
    setChunks([])
    setCursor(-1)

    // stream in chunks
    const stream = fetchStream('/api/article', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    })

    // add to list
    for (line of stream) {
      const data = JSON.parse(line)
      setChunks(cs => [...cs, data])
    }
  }

  // add keybindings
  useEffect(() => {
    function handleKeyDown(e) {
      console.log(e.key)
      if (e.key === 'ArrowDown') {
        setCursor(c => Math.min(c + 1, chunks.length))
      } else if (e.key === 'ArrowUp') {
        setCursor(c => Math.max(-1, c - 1))
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [chunks])

  return (
    <div className="flex flex-row h-screen w-screen">
      <div className="flex flex-col flex-1 h-full">
        <div className="relative flex flex-row border-b border-gray-200">
          <input type="text" className="w-full p-2 outline-none font-mono bg-gray-100" ref={inputRef} />
          <div className="absolute right-0 h-full p-2">
            <button className="px-1 bg-blue-500 text-white h-full w-full rounded-sm font-bold text-sm" onClick={handleTranslate}>Translate</button>
          </div>
        </div>
        <div className="flex flex-col flex-1 w-full gap-2 p-2">
          {chunks.map(([orig, trans], index) => (
            <div key={index} className={`flex flex-row p-2 w-full border rounded-sm ${cursor === index ? 'border-blue-500' : 'border-gray-200'}`}>
              <div className="w-[50%] mr-1 border-r border-gray-200">{orig}</div>
              <div className="w-[50%] ml-1">
                <span className={index > cursor ? 'bg-gray-100 text-gray-100' : ''}>{trans}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="w-[400px] h-full border-l border-gray-200 p-2">{article}</div>
    </div>
  )
}

export default App
