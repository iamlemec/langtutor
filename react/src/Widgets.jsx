// widgets

import { useState } from 'react'

function LangButton({ children, size, onClick, toggled }) {
  return <button
    onClick={onClick}
    className={`flex w-${size} h-${size} p-1 items-center justify-center font-bold border border-gray-300 rounded hover:bg-gray-300 ${toggled ? 'bg-gray-300' : ''}`}
  >
    {children}
  </button>
}

function SvgIcon({ svg, size = 4 }) {
  return <img src={svg} alt="svg" className={`w-${size} h-${size}`} />
}

export { LangButton, SvgIcon }
