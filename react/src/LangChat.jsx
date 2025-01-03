// LangChat component

import { useRef } from 'react'
import { marked } from 'marked'

function LangMessage({ role, children }) {
  return <div className="relative flex flex-row gap-2 border rounded p-2 pt-3">
    <div className="absolute top-[-8px] left-[7px] border rounded border-gray-300 text-xs px-1 bg-gray-100 small-caps font-bold">
      <div className="mt-[-2px]">{role}</div>
    </div>
    {children}
  </div>
}

function LangPrompt({ onSubmit }) {
  const queryRef = useRef(null)

  function handleKeyDown(event) {
    if (event.key === 'Enter') {
      const query = queryRef.current.value
      onSubmit(query)
    }
  }

  return <LangMessage role="user">
    <input ref={queryRef} type="text" className="w-full outline-none" onKeyDown={handleKeyDown} />
  </LangMessage>
}

export default function LangChat({ messages, onSubmit, generating }) {
  return <div className="flex flex-col gap-4 px-2 py-4">
    {messages.map(({role, content}, index) =>
      <LangMessage key={index} role={role}>
        <div className="markdown" dangerouslySetInnerHTML={{ __html: marked(content, {breaks: true}) }} />
      </LangMessage>
    )}
    {!generating && <LangPrompt key={messages.length} onSubmit={onSubmit} />}
  </div>
}
