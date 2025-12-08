package main

import (
	"log"
	"math"
	"os"
	"strconv"
)

func main() {
	if len(os.Args) < 2 {
		log.Print("Usage: go run converter.go <u64_value>")
		log.Print("Example: go run converter.go 4633390450058453230")
		return
	}

	params := len(os.Args[1:])
	for i := 0; i < params; i++ {
		u64Str := os.Args[i+1]
		u64Val, err := strconv.ParseUint(u64Str, 10, 64)
		if err != nil {
			log.Fatalf("Error: Invalid uint64 value '%s'", u64Str)
		}
		res := math.Float64frombits(u64Val)
		log.Printf("v:\t%s, IEEE 754 float:\t%.5f", u64Str, res)
	}
}
