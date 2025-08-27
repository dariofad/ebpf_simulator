package main

import (
	"bytes"
	"encoding/json"
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
	err := conn.SetReadDeadline(time.Now().Add(10 * time.Second))
	if err != nil {
		log.Println("ReadDeadline set error:", err)
		return
	}

	var rawJson []byte
	chunk := make([]byte, 16)

	for {
		n, err := conn.Read(chunk)
		rawJson = append(rawJson, chunk[:n]...)
		//log.Println(string(chunk[:n]))
		if err != nil {
			if err == io.EOF {
				log.Println("io.EOF reached")
				break
			}
			log.Println("Chunk reading error:", err)
			return
		}
	}
	rawJson = bytes.Trim(rawJson, "\x00")
	payload := make(map[string]interface{})
	err = json.Unmarshal(rawJson, &payload)
	if err != nil {
		log.Println("Invalid json:", err)
	} else {
		log.Println("Payload recovered, %d bytes", len(rawJson))
		//log.Println(string(rawJson))
	}

	// response := []byte{0x1}
	// _, err = conn.Write(response)
	// if err != nil {
	// 	log.Println("Error writing response", err)
	// 	return
	// }
	// log.Println("Response sent, closing the connection")

}
