// TransList component

import { useEffect, useRef, useState } from 'react'

function LangTooltip({ position, onMouseDown }) {
  return <div className="absolute flex w-6 h-6 bg-gray-100 border border-gray-400 rounded p-1 items-center justify-center cursor-default hover:bg-gray-300" style={{ left: position.x, top: position.y }} onMouseDown={onMouseDown}>
    <span className="font-bold">?</span>
  </div>
}

export default function LangList({ chunks, cursor, setCursor, viewing, handleGenerate }) {
  const listRefs = useRef([])
  const boxRef = useRef(null)
  const [showTooltip, setShowTooltip] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const timeoutRef = useRef(null)

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

  // show tooltip on selection
  function handleMouseUp(event) {
    // clear timeout if it exists
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // possibly show the tooltip after 100ms
    timeoutRef.current = setTimeout(() => {
      const selected = window.getSelection();
      const text = selected ? selected.toString().trim() : null
      if (text && text.length > 0) {
        const range = selected.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        setPosition({
          x: rect.left + rect.width - 24,
          y: rect.bottom + 5
        });
        setShowTooltip(true);
      } else {
        setShowTooltip(false);
      }
    }, 100);
  }

  // close tooltip when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (!boxRef.current.contains(event.target)) {
        setShowTooltip(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, []);

  // send question query
  function handleQuestion(event) {
    const selected = window.getSelection();
    const text = selected ? selected.toString().trim() : null
    console.log('handleQuestion', text)
    if (!text) return
    const question = `What is the meaning of the phrase "${text}"?`
    handleGenerate(question)
  }

  return (
    <div ref={boxRef} className="flex flex-col h-full w-full gap-2 p-2 overflow-y-scroll no-scrollbar" onMouseUp={handleMouseUp}>
      {chunks.map(([orig, trans], index) => (
        <div
          key={index}
          onMouseDown={e => setCursor(index)}
          ref={el => listRefs.current[index] = el}
          className={`flex flex-row p-2 w-full border rounded-sm ${cursor === index ? 'border-blue-500' : 'border-gray-200'}`}
        >
          <div className="w-[50%] pr-2 border-r border-gray-200">{orig}</div>
          <div className="w-[50%] pl-2">
            <span className={ viewing && index > cursor ? 'bg-gray-100 text-gray-100' : ''}>{trans}</span>
          </div>
        </div>
      ))}
      {showTooltip && <LangTooltip position={position} onMouseDown={handleQuestion} />}
    </div>
  )
}
