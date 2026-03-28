'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Database, Sparkles, Code2, BarChart3, MessageSquare, Plus, Menu, X, Trash2, Download, Share2, Lightbulb, Table, Image as ImageIcon } from 'lucide-react'
import { ChartRenderer } from '@/components/ChartRenderer'
import { DashboardRenderer } from '@/components/DashboardRenderer'
import { SqlCodeBlock } from '@/components/SqlCodeBlock'
import { exportChartAsPNG, exportDashboardAsPNG } from '@/lib/chartExport'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  data?: any[]
  chart?: any
  dashboard?: any
  explanation?: any
  timestamp: Date
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  timestamp: Date
}

interface StreamEvent {
  event: 'thinking' | 'querying' | 'visualizing' | 'complete' | 'error' | 'clarification'
  data: any
}

const EXAMPLE_QUERIES = [
  "What are the top 10 most ordered products?",
  "Which department has the highest reorder rate?",
  "Show me orders by hour of day",
  "Show me which aisles have the highest reorder rate and how that correlates with average basket position",
  "Analyze the distribution of basket positions across all 32 million prior orders",
]

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentStatus, setCurrentStatus] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [isInitialized, setIsInitialized] = useState(false)
  const [showDataTable, setShowDataTable] = useState<{[key: string]: boolean}>({})
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load conversations from localStorage on mount
  useEffect(() => {
    const loadConversations = () => {
      try {
        const savedConversations = localStorage.getItem('bi-agent-conversations')
        const savedCurrentId = localStorage.getItem('bi-agent-current-id')

        if (savedConversations) {
          const parsed = JSON.parse(savedConversations)
          // Convert timestamp strings back to Date objects
          const conversationsWithDates = parsed.map((conv: any) => ({
            ...conv,
            timestamp: new Date(conv.timestamp),
            messages: conv.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp)
            }))
          }))
          setConversations(conversationsWithDates)

          if (savedCurrentId && conversationsWithDates.find((c: Conversation) => c.id === savedCurrentId)) {
            setCurrentConversationId(savedCurrentId)
            const currentConv = conversationsWithDates.find((c: Conversation) => c.id === savedCurrentId)
            if (currentConv) {
              setMessages(currentConv.messages)
            }
          }
        }
      } catch (error) {
        console.error('Failed to load conversations from localStorage:', error)
      } finally {
        setIsInitialized(true)
      }
    }

    loadConversations()
  }, [])

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    if (isInitialized) {
      try {
        localStorage.setItem('bi-agent-conversations', JSON.stringify(conversations))
      } catch (error) {
        console.error('Failed to save conversations to localStorage:', error)
      }
    }
  }, [conversations, isInitialized])

  // Save current conversation ID to localStorage
  useEffect(() => {
    if (isInitialized) {
      try {
        if (currentConversationId) {
          localStorage.setItem('bi-agent-current-id', currentConversationId)
        } else {
          localStorage.removeItem('bi-agent-current-id')
        }
      } catch (error) {
        console.error('Failed to save current conversation ID:', error)
      }
    }
  }, [currentConversationId, isInitialized])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentStatus])

  const createNewConversation = () => {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: 'New conversation',
      messages: [],
      timestamp: new Date(),
    }
    setConversations(prev => [newConv, ...prev])
    setCurrentConversationId(newConv.id)
    setMessages([])
  }

  const switchConversation = (convId: string) => {
    const conv = conversations.find(c => c.id === convId)
    if (conv) {
      setCurrentConversationId(convId)
      setMessages(conv.messages)
    }
  }

  const deleteConversation = (convId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const updatedConversations = conversations.filter(c => c.id !== convId)
    setConversations(updatedConversations)

    // If we're deleting the current conversation, switch to the most recent one or clear
    if (convId === currentConversationId) {
      if (updatedConversations.length > 0) {
        const mostRecent = updatedConversations[0]
        setCurrentConversationId(mostRecent.id)
        setMessages(mostRecent.messages)
      } else {
        setCurrentConversationId('')
        setMessages([])
      }
    }
  }

  const updateConversationTitle = (convId: string, firstQuestion: string) => {
    setConversations(prev =>
      prev.map(conv =>
        conv.id === convId
          ? { ...conv, title: firstQuestion.slice(0, 50) + (firstQuestion.length > 50 ? '...' : '') }
          : conv
      )
    )
  }

  // Export data to CSV
  const exportToCSV = (data: any[], filename: string) => {
    if (!data || data.length === 0) return

    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => {
        const value = row[header]
        // Escape values containing commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`
        }
        return value
      }).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  // Export chart to PNG
  const exportChartToPNG = (messageId: string, title: string) => {
    const chartElement = document.getElementById(`chart-${messageId}`)
    if (!chartElement) return

    // Use html2canvas library (we'll need to install it)
    // For now, just show a message
    alert('Chart export will be available after installing html2canvas library. The data can be exported as CSV using the CSV button.')
  }

  // Copy query link to clipboard
  const shareQuery = async (message: Message) => {
    const queryData = {
      question: messages.find(m => m.type === 'user' &&
        messages.indexOf(m) === messages.indexOf(message) - 1)?.content || '',
      sql: message.explanation?.sql_query || '',
      chart: message.chart,
    }

    const shareText = `Question: ${queryData.question}\n\nSQL:\n${queryData.sql}\n\nView in BI Agent: ${window.location.origin}`

    try {
      await navigator.clipboard.writeText(shareText)
      setCopiedMessageId(message.id)
      setTimeout(() => setCopiedMessageId(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  // Generate query suggestions based on current result
  const getQuerySuggestions = (message: Message): string[] => {
    const userMessage = messages[messages.indexOf(message) - 1]?.content || ''

    // Smart suggestions based on the query type - only suggest queries that will work
    if (userMessage.toLowerCase().includes('department')) {
      return [
        'Which aisles are most popular?',
        'Show me the top 10 most ordered products',
        'What are the reorder rates by aisle?',
      ]
    }

    if (userMessage.toLowerCase().includes('product') || userMessage.toLowerCase().includes('banana')) {
      return [
        'Which department has the highest reorder rate?',
        'Show orders by hour of day',
        'What are the top 10 most ordered products?',
      ]
    }

    if (userMessage.toLowerCase().includes('aisle')) {
      return [
        'Which department has the most aisles?',
        'Show me the reorder rate by department',
        'What are the top products in this aisle?',
      ]
    }

    if (userMessage.toLowerCase().includes('order') || userMessage.toLowerCase().includes('hour')) {
      return [
        'What\'s the average basket size per order?',
        'Which department has the highest reorder rate?',
        'Show me the top 10 most ordered products',
      ]
    }

    // Default suggestions that always work
    return [
      'What are the top 10 most ordered products?',
      'Which department has the highest reorder rate?',
      'Show orders by hour of day',
    ]
  }

  // Toggle data table view
  const toggleDataTable = (messageId: string) => {
    setShowDataTable(prev => ({ ...prev, [messageId]: !prev[messageId] }))
  }

  const handleSubmit = async (question?: string) => {
    const queryText = question || input
    if (!queryText.trim() || isLoading) return

    // Create new conversation if none exists
    if (!currentConversationId) {
      const newConv: Conversation = {
        id: Date.now().toString(),
        title: queryText.slice(0, 50) + (queryText.length > 50 ? '...' : ''),
        messages: [],
        timestamp: new Date(),
      }
      setConversations(prev => [newConv, ...prev])
      setCurrentConversationId(newConv.id)
    } else if (messages.length === 0) {
      // Update title for first message
      updateConversationTitle(currentConversationId, queryText)
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: queryText,
      timestamp: new Date(),
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)
    setCurrentStatus('Thinking...')

    try {
      const response = await fetch('http://localhost:8000/query/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: queryText,
          conversation_id: currentConversationId,
          include_explanation: true,
        }),
      })

      if (!response.ok) {
        throw new Error('Query failed')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue

          const data = line.slice(6)
          try {
            const event: StreamEvent = JSON.parse(data)

            if (event.event === 'thinking') {
              setCurrentStatus(event.data.message || 'Analyzing...')
            } else if (event.event === 'querying') {
              setCurrentStatus('Executing query...')
            } else if (event.event === 'visualizing') {
              setCurrentStatus('Creating visualization...')
            } else if (event.event === 'clarification') {
              // LLM needs clarification - show as a normal assistant message
              const clarificationMessage: Message = {
                id: Date.now().toString(),
                type: 'assistant',
                content: event.data.message,
                timestamp: new Date(),
              }

              const updatedMessages = [...newMessages, clarificationMessage]
              setMessages(updatedMessages)

              // Update conversation in history
              setConversations(prev =>
                prev.map(conv =>
                  conv.id === currentConversationId
                    ? { ...conv, messages: updatedMessages, timestamp: new Date() }
                    : conv
                )
              )

              setCurrentStatus('')
              setIsLoading(false)
            } else if (event.event === 'complete') {
              const result = event.data

              const assistantMessage: Message = {
                id: Date.now().toString(),
                type: 'assistant',
                content: `Found ${result.result.row_count} results in ${result.result.execution_time_ms.toFixed(0)}ms`,
                data: result.result.data,
                chart: result.chart,
                dashboard: result.dashboard,
                explanation: result.explanation,
                timestamp: new Date(),
              }

              const updatedMessages = [...newMessages, assistantMessage]
              setMessages(updatedMessages)

              // Update conversation in history
              setConversations(prev =>
                prev.map(conv =>
                  conv.id === currentConversationId
                    ? { ...conv, messages: updatedMessages, timestamp: new Date() }
                    : conv
                )
              )

              setCurrentStatus('')
              setIsLoading(false)
            } else if (event.event === 'error') {
              throw new Error(event.data.message || 'Query failed')
            }
          } catch (parseError) {
            console.error('Failed to parse event:', parseError)
          }
        }
      }
    } catch (error) {
      console.error('Query error:', error)
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
      setCurrentStatus('')
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-72' : 'w-0'
        } transition-all duration-300 bg-secondary/30 backdrop-blur-xl border-r border-border/50 overflow-hidden flex flex-col`}
      >
        <div className="p-4 border-b border-border/50">
          <button
            onClick={createNewConversation}
            className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-primary to-primary/90 text-primary-foreground rounded-xl hover:shadow-lg hover:shadow-primary/20 transition-all duration-200 hover:scale-[1.02] font-medium"
          >
            <Plus className="w-4 h-4" />
            <span>New Conversation</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          {conversations.length === 0 ? (
            <div className="text-center py-8 px-4">
              <MessageSquare className="w-8 h-8 text-muted-foreground/40 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">No conversations yet</p>
              <p className="text-xs text-muted-foreground/60 mt-1">Start a new chat to begin</p>
            </div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`relative group rounded-xl mb-2 transition-all duration-200 ${
                  conv.id === currentConversationId
                    ? 'bg-primary/15 border border-primary/30 shadow-sm'
                    : 'hover:bg-secondary/50 border border-transparent'
                }`}
              >
                <button
                  onClick={() => switchConversation(conv.id)}
                  className="w-full text-left px-3 py-3"
                >
                  <div className="flex items-start space-x-3">
                    <div className={`p-1.5 rounded-lg mt-0.5 ${
                      conv.id === currentConversationId
                        ? 'bg-primary/20'
                        : 'bg-secondary/80'
                    }`}>
                      <MessageSquare className={`w-3.5 h-3.5 ${
                        conv.id === currentConversationId
                          ? 'text-primary'
                          : 'text-muted-foreground'
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0 pr-6">
                      <p className={`text-sm font-medium truncate ${
                        conv.id === currentConversationId
                          ? 'text-primary'
                          : 'text-foreground'
                      }`}>
                        {conv.title}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {conv.messages.length} {conv.messages.length === 1 ? 'message' : 'messages'}
                      </p>
                    </div>
                  </div>
                </button>
                <button
                  onClick={(e) => deleteConversation(conv.id, e)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 transition-all duration-200"
                  title="Delete conversation"
                >
                  <Trash2 className="w-3.5 h-3.5 text-red-400 hover:text-red-300" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b border-border/50 bg-background/95 backdrop-blur-md sticky top-0 z-10 shadow-lg shadow-black/5">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 hover:bg-secondary/50 rounded-lg transition-all duration-200 hover:scale-105"
                >
                  {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                </button>
                <div className="p-2.5 bg-gradient-to-br from-primary to-primary/80 rounded-xl shadow-lg shadow-primary/20">
                  <Database className="w-5 h-5 text-primary-foreground" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-foreground tracking-tight">
                    Conversational BI Agent
                  </h1>
                  <p className="text-xs text-muted-foreground">
                    Natural language analytics powered by AI
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary text-xs font-semibold rounded-full border border-primary/20">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Analytics</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full space-y-12 py-12">
                <div className="text-center space-y-6">
                  <div className="relative">
                    <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full"></div>
                    <div className="relative inline-flex p-6 bg-gradient-to-br from-primary/20 to-primary/5 rounded-2xl border border-primary/20">
                      <BarChart3 className="w-16 h-16 text-primary" />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <h2 className="text-4xl font-bold text-foreground bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
                      Conversational BI Agent
                    </h2>
                    <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                      Ask questions in natural language and get instant insights from 3.4M orders
                    </p>
                  </div>
                  <div className="flex items-center justify-center gap-6 text-sm">
                    <div className="flex items-center gap-2 px-4 py-2 bg-secondary/50 rounded-lg border border-border/50">
                      <Database className="w-4 h-4 text-primary" />
                      <span className="text-foreground/80">3.4M+ Orders</span>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 bg-secondary/50 rounded-lg border border-border/50">
                      <Code2 className="w-4 h-4 text-primary" />
                      <span className="text-foreground/80">50K+ Products</span>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 bg-secondary/50 rounded-lg border border-border/50">
                      <Sparkles className="w-4 h-4 text-primary" />
                      <span className="text-foreground/80">AI-Powered</span>
                    </div>
                  </div>
                </div>

                <div className="w-full max-w-3xl space-y-4">
                  <h3 className="text-sm font-semibold text-foreground/60 uppercase tracking-wide text-center">
                    Try these example queries
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {EXAMPLE_QUERIES.map((query, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSubmit(query)}
                        className="group p-4 text-left bg-secondary/50 hover:bg-secondary rounded-xl transition-all duration-200 border border-border/50 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5"
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-1.5 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                            <BarChart3 className="w-4 h-4 text-primary" />
                          </div>
                          <div className="text-sm font-medium text-foreground group-hover:text-primary/90 transition-colors">
                            {query}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
              >
                <div
                  className={`w-full ${
                    message.type === 'user'
                      ? 'bg-gradient-to-br from-primary to-primary/90 text-primary-foreground max-w-4xl shadow-lg shadow-primary/10'
                      : 'bg-secondary/50 border border-border/50'
                  } rounded-2xl p-5 space-y-4`}
                >
                  <div className="flex items-start space-x-3">
                    {message.type === 'assistant' && (
                      <div className="p-2 bg-gradient-to-br from-primary/20 to-primary/10 rounded-xl mt-0.5 border border-primary/20">
                        <Sparkles className="w-4 h-4 text-primary" />
                      </div>
                    )}
                    <div className="flex-1 space-y-4">
                      <p className="text-sm leading-relaxed">{message.content}</p>

                      {message.explanation && (
                        <details className="text-xs space-y-2">
                          <summary className="cursor-pointer flex items-center space-x-2 font-medium hover:text-primary transition-colors">
                            <Code2 className="w-4 h-4" />
                            <span>View SQL & Reasoning</span>
                          </summary>
                          <div className="mt-3 space-y-3">
                            <div>
                              <div className="font-semibold mb-2 text-foreground/80">Reasoning:</div>
                              <div className="text-muted-foreground text-sm leading-relaxed">
                                {message.explanation.reasoning}
                              </div>
                            </div>
                            <div>
                              <div className="font-semibold mb-2 text-foreground/80">SQL Query:</div>
                              <SqlCodeBlock code={message.explanation.sql_query} />
                            </div>
                            <div className="flex items-center space-x-4 text-muted-foreground pt-2">
                              <span className="flex items-center gap-1">
                                <Database className="w-3 h-3" />
                                Tables: {message.explanation.tables_used.join(', ')}
                              </span>
                              <span>Complexity: {message.explanation.complexity}</span>
                            </div>
                          </div>
                        </details>
                      )}

                      {message.dashboard && message.data ? (
                        <div className="bg-background/80 backdrop-blur-sm rounded-xl p-5 border border-border/30 shadow-lg space-y-4 overflow-visible">
                          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                            <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
                              <BarChart3 className="w-4 h-4 text-primary flex-shrink-0" />
                              Dashboard View
                            </h3>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => exportDashboardAsPNG(`dashboard-${message.id}`, message.dashboard.title.replace(/\s+/g, '_'))}
                                className="p-2 hover:bg-secondary/50 rounded-lg transition-all duration-200 hover:scale-105 group"
                                title="Export dashboard as image"
                              >
                                <ImageIcon className="w-4 h-4 text-muted-foreground group-hover:text-primary" />
                              </button>
                              <button
                                onClick={() => exportToCSV(message.data!, `${message.dashboard.title.replace(/\s+/g, '_')}`)}
                                className="p-2 hover:bg-secondary/50 rounded-lg transition-all duration-200 hover:scale-105 group"
                                title="Export data as CSV"
                              >
                                <Download className="w-4 h-4 text-muted-foreground group-hover:text-primary" />
                              </button>
                              <button
                                onClick={() => shareQuery(message)}
                                className="p-2 hover:bg-secondary/50 rounded-lg transition-all duration-200 hover:scale-105 group relative"
                                title="Share query"
                              >
                                <Share2 className="w-4 h-4 text-muted-foreground group-hover:text-primary" />
                                {copiedMessageId === message.id && (
                                  <span className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-primary text-primary-foreground text-xs rounded whitespace-nowrap">
                                    Copied!
                                  </span>
                                )}
                              </button>
                            </div>
                          </div>

                          <div id={`dashboard-${message.id}`}>
                            <DashboardRenderer data={message.data} dashboard={message.dashboard} />
                          </div>
                        </div>
                      ) : message.chart && message.data ? (
                        <div className="bg-background/80 backdrop-blur-sm rounded-xl p-5 border border-border/30 shadow-lg space-y-4">
                          <div className="flex items-center justify-between">
                            <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
                              <BarChart3 className="w-4 h-4 text-primary" />
                              {message.chart.title}
                            </h3>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleDataTable(message.id)}
                                className="p-2 hover:bg-secondary/50 rounded-lg transition-all duration-200 hover:scale-105 group"
                                title="Toggle data table view"
                              >
                                <Table className="w-4 h-4 text-muted-foreground group-hover:text-primary" />
                              </button>
                              {!showDataTable[message.id] && (
                                <button
                                  onClick={() => exportChartAsPNG(`chart-${message.id}`, message.chart.title.replace(/\s+/g, '_'))}
                                  className="p-2 hover:bg-secondary/50 rounded-lg transition-all duration-200 hover:scale-105 group"
                                  title="Export chart as image"
                                >
                                  <ImageIcon className="w-4 h-4 text-muted-foreground group-hover:text-primary" />
                                </button>
                              )}
                              <button
                                onClick={() => exportToCSV(message.data!, `${message.chart.title.replace(/\s+/g, '_')}`)}
                                className="p-2 hover:bg-secondary/50 rounded-lg transition-all duration-200 hover:scale-105 group"
                                title="Export data as CSV"
                              >
                                <Download className="w-4 h-4 text-muted-foreground group-hover:text-primary" />
                              </button>
                              <button
                                onClick={() => shareQuery(message)}
                                className="p-2 hover:bg-secondary/50 rounded-lg transition-all duration-200 hover:scale-105 group relative"
                                title="Share query"
                              >
                                <Share2 className="w-4 h-4 text-muted-foreground group-hover:text-primary" />
                                {copiedMessageId === message.id && (
                                  <span className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-primary text-primary-foreground text-xs rounded whitespace-nowrap">
                                    Copied!
                                  </span>
                                )}
                              </button>
                            </div>
                          </div>

                          {showDataTable[message.id] ? (
                            <div className="overflow-x-auto max-h-[600px]">
                              <table className="w-full text-xs">
                                <thead className="sticky top-0 bg-background/95 backdrop-blur-sm z-10">
                                  <tr className="border-b border-border/30">
                                    {Object.keys(message.data[0] || {}).map((key) => (
                                      <th key={key} className="text-left p-2 font-semibold text-foreground/80">
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {message.data.slice(0, 100).map((row, idx) => (
                                    <tr key={idx} className="border-b border-border/10 hover:bg-secondary/20">
                                      {Object.values(row).map((value: any, vidx) => (
                                        <td key={vidx} className="p-2 text-foreground/70">
                                          {typeof value === 'number' ? value.toLocaleString() : value}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                              {message.data.length > 200 && (
                                <p className="text-xs text-muted-foreground mt-2 text-center py-2 sticky bottom-0 bg-background/95">
                                  Showing first 200 of {message.data.length.toLocaleString()} rows. Export CSV to see all data.
                                </p>
                              )}
                            </div>
                          ) : (
                            <div id={`chart-${message.id}`}>
                              <ChartRenderer
                                data={message.data.length > 1000 ? message.data.slice(0, 1000) : message.data}
                                config={message.chart}
                              />
                              {message.data.length > 1000 && (
                                <p className="text-xs text-muted-foreground mt-2 text-center">
                                  Chart showing first 1,000 of {message.data.length.toLocaleString()} rows. Toggle table view or export CSV for full data.
                                </p>
                              )}
                            </div>
                          )}

                          {/* Natural language interpretation for single charts */}
                          {message.chart?.interpretation && (
                            <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mt-4">
                              <div className="flex items-start gap-3">
                                <div className="flex-shrink-0 mt-0.5">
                                  <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                </div>
                                <div>
                                  <h4 className="text-sm font-semibold text-foreground mb-1">Insights</h4>
                                  <p className="text-sm text-muted-foreground leading-relaxed">
                                    {message.chart.interpretation}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : null}

                      {message.type === 'assistant' && message.data && (
                        <div className="pt-2">
                          <div className="flex items-center gap-2 mb-2">
                            <Lightbulb className="w-3.5 h-3.5 text-primary" />
                            <span className="text-xs font-semibold text-foreground/60">Related queries you might like:</span>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {getQuerySuggestions(message).map((suggestion, idx) => (
                              <button
                                key={idx}
                                onClick={() => {
                                  setInput(suggestion)
                                  document.querySelector<HTMLInputElement>('input[type="text"]')?.focus()
                                }}
                                className="text-xs px-3 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-all duration-200 hover:scale-105 border border-primary/20"
                              >
                                {suggestion}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {isLoading && currentStatus && (
              <div className="flex justify-start animate-fade-in">
                <div className="bg-secondary/50 border border-border/50 rounded-2xl p-5 flex items-center space-x-3">
                  <div className="relative">
                    <div className="absolute inset-0 bg-primary/20 blur-md rounded-full"></div>
                    <Loader2 className="relative w-5 h-5 animate-spin text-primary" />
                  </div>
                  <span className="text-sm text-foreground font-medium">{currentStatus}</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-border/50 bg-background/95 backdrop-blur-md shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)]">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex space-x-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !isLoading && input.trim() && handleSubmit()}
                  placeholder="Ask a question about your data..."
                  disabled={isLoading}
                  className="w-full px-5 py-3.5 bg-secondary/50 border border-border/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 disabled:opacity-50 transition-all duration-200 placeholder:text-muted-foreground/50"
                />
              </div>
              <button
                onClick={() => handleSubmit()}
                disabled={isLoading || !input.trim()}
                className="px-6 py-3.5 bg-gradient-to-r from-primary to-primary/90 text-primary-foreground rounded-xl hover:shadow-lg hover:shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-[1.02] disabled:hover:scale-100 flex items-center space-x-2 font-medium"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span className="hidden sm:inline">Processing</span>
                  </>
                ) : (
                  <>
                    <span className="hidden sm:inline">Send</span>
                    <Send className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
