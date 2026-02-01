import { useEffect, useState, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'

export function useWebSocket(tenantId) {
    const [lastMessage, setLastMessage] = useState(null)
    const [isConnected, setIsConnected] = useState(false)
    const wsRef = useRef(null)
    const queryClient = useQueryClient()
    const reconnectTimeoutRef = useRef(null)
    const reconnectAttempts = useRef(0)
    const maxReconnectAttempts = 5

    useEffect(() => {
        if (!tenantId) return

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
            const wsUrl = `${protocol}//${window.location.host}/ws/${tenantId}`

            console.log('Connecting to WebSocket:', wsUrl)
            const ws = new WebSocket(wsUrl)
            wsRef.current = ws

            ws.onopen = () => {
                console.log('WebSocket connected')
                setIsConnected(true)
                reconnectAttempts.current = 0
            }

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    setLastMessage(data)

                    // Handle different message types
                    switch (data.type) {
                        case 'action.proposed':
                            toast.success('New action requires approval', {
                                icon: '📋',
                            })
                            queryClient.invalidateQueries(['actions'])
                            break

                        case 'intent.updated':
                            queryClient.invalidateQueries(['accounts'])
                            queryClient.invalidateQueries(['metrics'])
                            break

                        case 'signal.received':
                            queryClient.invalidateQueries(['signals'])
                            queryClient.invalidateQueries(['accounts'])
                            break

                        default:
                            console.log('Unknown message type:', data.type)
                    }
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error)
                }
            }

            ws.onerror = (error) => {
                console.error('WebSocket error:', error)
            }

            ws.onclose = () => {
                console.log('WebSocket disconnected')
                setIsConnected(false)

                // Attempt to reconnect with exponential backoff
                if (reconnectAttempts.current < maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
                    console.log(`Reconnecting in ${delay}ms...`)

                    reconnectTimeoutRef.current = setTimeout(() => {
                        reconnectAttempts.current++
                        connect()
                    }, delay)
                } else {
                    toast.error('Lost connection to server. Please refresh the page.')
                }
            }
        }

        connect()

        // Keepalive ping every 30 seconds
        const pingInterval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send('ping')
            }
        }, 30000)

        return () => {
            clearInterval(pingInterval)
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current)
            }
            if (wsRef.current) {
                wsRef.current.close()
            }
        }
    }, [tenantId, queryClient])

    return { lastMessage, isConnected }
}
