// LangChat component

function LangMessage({ role, children }) {
  return <div className="relative flex flex-row gap-2 border rounded p-2">
    <div className="absolute top-[-8px] left-[7px] border rounded border-gray-300 text-xs px-1 bg-gray-100 small-caps font-bold">
      <div className="mt-[-2px]">{role}</div>
    </div>
    {children}
  </div>
}

function LangPrompt() {
  return <LangMessage role="user">
    <input type="text" className="w-full outline-none"/>
  </LangMessage>
}

export default function LangChat({ messages }) {
  return <div className="flex flex-col gap-4 px-2 py-4">
    {messages.map(({role, content}, index) =>
      <LangMessage key={index} role={role}>
        <div className="[overflow-wrap:anywhere]">{content}</div>
      </LangMessage>
    )}
    <LangPrompt key={messages.length}/>
  </div>
}
