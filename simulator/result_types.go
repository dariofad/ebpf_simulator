package simulator

// mock result struct
type Result struct {
	AEgo []float64 `msgpack:"a_ego"`
	VEgo []float64 `msgpack:"v_ego"`
}

type ModelRecord struct {
	Time   uint32
	Filler uint32
	AEgo   float64
	VEgo   float64
}
