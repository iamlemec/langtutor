// TransList component

import { useEffect, useRef } from 'react'

export default function LangList({ chunks, cursor, setCursor }) {
  const listRefs = useRef([])

  // scroll to cursor
  useEffect(() => {
    if (cursor >= 0 && cursor < chunks.length) {
      listRefs.current[cursor].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      })
    }
  }, [cursor])

  // cursor navigation
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'ArrowDown') {
        console.log(cursor)
        if (cursor < chunks.length) {
          e.preventDefault()
          setCursor(c => c + 1)
        }
      } else if (e.key === 'ArrowUp') {
        console.log(cursor)
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
    <div className="flex flex-col flex-1 w-full gap-2 p-2">
      {chunks.map(([orig, trans], index) => (
        <div
          key={index}
          onMouseDown={e => setCursor(index)}
          ref={el => listRefs.current[index] = el}
          className={`flex flex-row p-2 w-full border rounded-sm ${cursor === index ? 'border-blue-500' : 'border-gray-200'}`}
        >
          <div className="w-[50%] mr-1 border-r border-gray-200">{orig}</div>
          <div className="w-[50%] ml-1">
            <span className={index > cursor ? 'bg-gray-100 text-gray-100' : ''}>{trans}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
