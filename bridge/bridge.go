package main

import (
	"bytes"
	"github.com/vmihailenco/msgpack/v5"
	"io"
	"log"
	"net"
	"time"
)

func main() {
	listener, err := net.Listen("tcp", ":8080")
	if err != nil {
		log.Fatal("Server cannot setup the listener")
	}
	defer listener.Close()
	log.Println("Server Listening on port 8080")

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Print("Error accepting connection", err)
			continue
		}

		go handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {

	defer conn.Close()
	err := conn.SetReadDeadline(time.Now().Add(15 * time.Second))
	if err != nil {
		log.Println("ReadDeadline set error:", err)
		return
	}

	var rawData []byte
	chunk := make([]byte, 16)

	for {
		n, err := conn.Read(chunk)
		rawData = append(rawData, chunk[:n]...)
		if err != nil {
			if err == io.EOF {
				log.Println("io.EOF reached")
				break
			}
			log.Println("Chunk reading error:", err)
			return
		}
	}
	payload := make(map[string]interface{})
	dec := msgpack.NewDecoder(bytes.NewReader(rawData))
	err = dec.Decode(&payload)
	if err != nil {
		log.Println("Invalid json:", err)
	} else {
		log.Println("Payload recovered, %d bytes", len(rawData))
		// log.Println(payload)
	}

	// response := []byte{0x1}
	// _, err = conn.Write(response)
	// if err != nil {
	// 	log.Println("Error writing response", err)
	// 	return
	// }
	// log.Println("Response sent, closing the connection")

}
