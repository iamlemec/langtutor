import { useState, useRef, useEffect } from 'react'
import './App.css'

import LangList from './LangList.jsx'
import LangChat from './LangChat.jsx'
import { useError } from './Error.jsx'
import { LangButton, SvgIcon } from './Widgets.jsx'
import { fetchTextStream, fetchJsonStream } from './utils.jsx'

import eyeOpen from './icons/eye_open.svg'

function App() {
  const [article, setArticle] = useState(null)
  const [chunks, setChunks] = useState([])
  const [cursor, setCursor] = useState(-1)
  const [messages, setMessages] = useState([])
  const [translating, setTranslating] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [viewing, setViewing] = useState(false)
  const [selected, setSelected] = useState(null);
  const inputRef = useRef(null)
  const { showError } = useError()

  // capture selection
  useEffect(() => {
    function handleSelection() {
      const selection = window.getSelection()
      const text = selection.toString().trim()
      setSelected(text)
    }
    window.addEventListener('mouseup', handleSelection)
    return () => window.removeEventListener('mouseup', handleSelection)
  }, [])

  // capture question mark
  useEffect(() => {
    function handleKeydown(event) {
      if (event.target.tagName == 'TEXTAREA') return
      if (event.key === '?') {
        const question = selected ?
          `What is the meaning of the phrase "${selected}"?` :
          'What is the meaning of the current sentence?'
        handleGenerate(question)
      }
    }
    window.addEventListener('keydown', handleKeydown)
    return () => window.removeEventListener('keydown', handleKeydown)
  }, [selected])

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
      showError(err.message)
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
      showError(err.message)
    }

    // show prompt
    setGenerating(false)
  }

  return (
    <div className="flex flex-row h-screen w-screen">
      <div className="flex flex-col flex-1 h-full">
        <div className="relative flex flex-row gap-2 p-2 items-center border-b border-gray-300 bg-gray-100">
          <input ref={inputRef} type="text" className="w-full outline-none font-mono bg-gray-100" placeholder="Enter article url" />
          <LangButton onClick={() => setViewing(!viewing)} toggled={viewing}>
            <SvgIcon svg={eyeOpen} size={4} />
          </LangButton>
          <button className={`px-1 bg-blue-500 text-white h-full rounded-sm font-bold text-sm ${translating ? 'opacity-50' : ''}`} disabled={translating} onClick={handleTranslate}>Translate</button>
        </div>
        <div className="flex-1 w-full min-h-0">
          <LangList chunks={chunks} cursor={cursor} setCursor={setCursor} viewing={viewing} />
        </div>
      </div>
      <div className="w-[450px] h-full border-l border-gray-300 bg-gray-100">
        <LangChat messages={messages} onSubmit={handleGenerate} generating={generating} active={article !== null} />
      </div>
    </div>
  )
}

export default App
