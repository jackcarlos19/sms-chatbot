import * as React from 'react'

export function Main({
  children,
  className = '',
  fixed,
  fluid,
}: {
  children: React.ReactNode
  className?: string
  fixed?: boolean
  fluid?: boolean
}) {
  return (
    <main
      className={[
        'flex-1 px-4 py-6',
        fixed ? 'flex flex-col overflow-hidden' : '',
        fluid ? '' : '@container/content mx-auto max-w-7xl w-full',
        className,
      ].filter(Boolean).join(' ')}
    >
      {children}
    </main>
  )
}
