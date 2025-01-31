// LangChat component

import { useRef, useEffect } from 'react'
import { marked } from 'marked'

function LangBox({ role, children }) {
  return <div className="relative flex flex-row gap-2 border rounded-sm border-gray-300 p-2 pt-3">
    <div className="absolute top-[-8px] left-[7px] border rounded-sm border-gray-300 bg-white text-xs px-1 bg-gray-100 small-caps font-bold">
      <div className="mt-[-2px]">{role}</div>
    </div>
    {children}
  </div>
}

function LangPrompt({ onSubmit }) {
  const queryRef = useRef(null)

  function adjustHeight() {
    const textarea = queryRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter') {
      const query = queryRef.current.value
      onSubmit(query)
    }
  }

  useEffect(() => {
    adjustHeight();
  }, []);

  return <LangBox role="user">
    <textarea ref={queryRef} rows={1}className="w-full outline-none bg-gray-100 resize-none" onKeyDown={handleKeyDown} onChange={adjustHeight} />
  </LangBox>
}

function LangMessage({ role, content }) {
  return <LangBox role={role}>
    <div className="markdown" dangerouslySetInnerHTML={{ __html: marked(content, {breaks: true}) }} />
  </LangBox>
}

export default function LangChat({ messages, onSubmit, generating, active }) {
  const content = active ? 'Ask me anything about this article.' : 'Enter a URL and click "Translate" to start.'
  return <div className="flex flex-col h-full gap-4 px-2 py-4 overflow-y-auto">
    <LangMessage role="system" content={content} />
    {messages.map(({role, content}, index) =>
      <LangMessage key={index} role={role} content={content} />
    )}
    { active && !generating && <LangPrompt key={messages.length} onSubmit={onSubmit} />}
  </div>
}
