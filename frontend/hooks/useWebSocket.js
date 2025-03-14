import { useEffect, useRef } from 'react'

const useWebSocket = ( url, options = {}) => {
    const {onOpen, onMessage, onClose, onError, reconnectInterval = 3000, reconnectAttempts = 10} = options

    const socket = useRef(null)
    const reconnectCount = useRef(0)

    const connect = () => {
        socket.current = new WebSocket(url)

        socket.current.onopen = (event) => {
            console.log("Websocket Connected")
            reconnectCount.current = 0
            if (onOpen) onOpen(event)
        }

        socket.current.onmessage = (event) => {
            if (onmessage) onmessage(event.data)
        }

        socket.current.onclose = (event) => {
            console.log('Websocket Disconneted')
            if (onClose) onClose(event)

            // Attempt to reconnect
            if (reconnectCount.current < reconnectAttempts) {
                reconnectCount.current += 1
                console.log(`Attempting to reconnect (${reconnectCount.current}/${reconnectAttempts})...`)
                setTimeout(connect, reconnectInterval)
            }
        }

        socket.current.onerror = (error) => {
            console.error('WebSocket error:', error)
            if (onError) onError(error)
        }

    }

    useEffect(() => {
        connect()

        return () => {
            if (socket.current) {
                socket.current.close()
            }
        }
    }, [url])

    return {
        sendMessage: (data) => {
            if (socket.current && socket.current.readyState === WebSocket.OPEN) {
                socket.current.send(data)
                return true
            }
            return false
        }
    }

}


export default useWebSocket