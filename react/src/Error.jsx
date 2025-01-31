import React, { createContext, useContext, useCallback, useState } from 'react'

// Context
const ErrorContext = createContext(null)

// Close Icon Component
const CloseIcon = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    className="w-4 h-4"
  >
    <line x1="4" y1="4" x2="12" y2="12" />
    <line x1="4" y1="12" x2="12" y2="4" />
  </svg>
)

// Error Message Component
const ErrorMessage = ({ message, title = 'Error', id, onClose }) => {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 shadow-sm animate-in fade-in duration-300">
      <div className="flex justify-between items-center mb-2">
        <h4 className="text-sm font-semibold text-red-900 m-0">{title}</h4>
        <button
          onClick={onClose}
          className="text-red-900 hover:bg-red-100 rounded p-1 transition-colors duration-150"
          aria-label="Close error message"
        >
          <CloseIcon />
        </button>
      </div>
      <p className="text-sm text-red-800 m-0">{message}</p>
    </div>
  )
}

// Provider Component
export const ErrorProvider = ({ children }) => {
  const [errors, setErrors] = useState([])

  const showError = useCallback((message, title = 'Error', duration = 5000) => {
    const id = Date.now()
    setErrors(prev => [...prev, { id, message, title }])

    if (duration) {
      setTimeout(() => {
        removeError(id)
      }, duration)
    }

    return id
  }, [])

  const removeError = useCallback((id) => {
    setErrors(prev => prev.filter(error => error.id !== id))
  }, [])

  return (
    <ErrorContext.Provider value={{ showError, removeError }}>
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 max-w-md w-full">
        {errors.map(error => (
          <ErrorMessage
            key={error.id}
            message={error.message}
            title={error.title}
            onClose={() => removeError(error.id)}
          />
        ))}
      </div>
      {children}
    </ErrorContext.Provider>
  )
}

// Custom Hook
export const useError = () => {
  const context = useContext(ErrorContext)
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider')
  }
  return context
}
