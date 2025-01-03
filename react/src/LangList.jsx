// TransList component

import { useEffect, useRef } from 'react'

export default function LangList({ chunks, cursor, setCursor }) {
  const listRefs = useRef([])
  const boxRef = useRef(null)

  // scroll to bottom
  function scrollToBottom() {
    const box = boxRef.current
    box.scrollTo({
      top: box.scrollHeight,
      behavior: 'smooth',
    })
  }

  // scroll to top
  function scrollToTop() {
    const box = boxRef.current
    box.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }

  // scroll to cursor
  useEffect(() => {
    if (cursor >= 0 && cursor < chunks.length) {
      listRefs.current[cursor].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      })
    }
    if (cursor >= chunks.length - 1) {
      scrollToBottom()
    } else if (cursor <= 0) {
      scrollToTop()
    }
  }, [cursor])

  // cursor navigation
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'ArrowDown') {
        if (cursor < chunks.length) {
          e.preventDefault()
          setCursor(c => c + 1)
        }
      } else if (e.key === 'ArrowUp') {
        if (cursor > -1) {
          e.preventDefault()
          setCursor(c => c - 1)
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [chunks, cursor])
  
  return (
    <div ref={boxRef} className="flex flex-col h-full w-full gap-2 p-2 overflow-y-scroll">
      {chunks.map(([orig, trans], index) => (
        <div
          key={index}
          onMouseDown={e => setCursor(index)}
          ref={el => listRefs.current[index] = el}
          className={`flex flex-row p-2 w-full border rounded-sm ${cursor === index ? 'border-blue-500' : 'border-gray-200'}`}
        >
          <div className="w-[50%] pr-2 border-r border-gray-200">{orig}</div>
          <div className="w-[50%] pl-2">
            <span className={index > cursor ? 'bg-gray-100 text-gray-100' : ''}>{trans}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
