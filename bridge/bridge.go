package main

import (
	"bytes"
	"fmt"
	"io"
	"log"
	"net"
	"time"

	"github.com/vmihailenco/msgpack/v5"
)

type logWriter struct {
}

func (writer logWriter) Write(bytes []byte) (int, error) {
	return fmt.Print(time.Now().UTC().Format("04:05.000") +
		": " + string(bytes))
}

func main() {
	log.SetFlags(0)
	log.SetOutput(new(logWriter))
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
		log.Println("Connection accepted")

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
	chunk := make([]byte, 32768)

	for {
		n, err := conn.Read(chunk)
		rawData = append(rawData, chunk[:n]...)
		if err != nil {
			if err == io.EOF {
				log.Println("Payload received")
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
		log.Printf("Payload recovered, %.3f MB\n",
			float64(len(rawData))/(1024*1024))
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
