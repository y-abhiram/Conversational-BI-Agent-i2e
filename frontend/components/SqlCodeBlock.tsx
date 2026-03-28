'use client'

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface SqlCodeBlockProps {
  code: string
}

export function SqlCodeBlock({ code }: SqlCodeBlockProps) {
  // Ensure SQL ends with semicolon
  const formattedCode = code.trim().endsWith(';') ? code : `${code.trim()};`

  return (
    <div className="relative rounded-lg overflow-hidden">
      <SyntaxHighlighter
        language="sql"
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          padding: '1rem',
          fontSize: '0.875rem',
          borderRadius: '0.5rem',
          background: 'hsl(var(--background))',
          border: '1px solid hsl(var(--border))',
        }}
        showLineNumbers={false}
      >
        {formattedCode}
      </SyntaxHighlighter>
    </div>
  )
}
