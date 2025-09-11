package simulator

import (
	"encoding/json"
	"errors"
	"log"
	"os"
	"os/exec"
	"strconv"

	"github.com/cilium/ebpf"
	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/rlimit"
)

var VERBOSE bool

// Allow the simulator process to to lock memory for eBPF resources
func RemoveMemlock() {

	if err := rlimit.RemoveMemlock(); err != nil {
		log.Fatal(err)
	}
}

func Run(data map[string]interface{}) (*Result, error) {

	// Load eBPF collection spec
	spec, err := loadProbe()
	if err != nil {
		log.Printf("loading collectionSpec: %s", err)
		return nil, errors.New("Simulation failed: cannot retrieve collection spec")
	}

	// Get the binary path
	rawBinPath, err := os.ReadFile("simulator/.BIN_PATH")
	if err != nil {
		log.Print("Error setting the dualACC")
		return nil, errors.New("Simulation failed: cannot find the executable to simulate")
	}
	binPath := string(rawBinPath)
	log.Println("ACC binary path:", binPath)

	// Get the symbol name
	rawSymbol, err := os.ReadFile("simulator/.BIN_SYM")
	if err != nil {
		log.Print("Error setting the symbol name")
		return nil, errors.New("Simulation failed: cannot read the symbol name")
	}
	symbol := string(rawSymbol)
	log.Println("ACC symbol name:", symbol)

	// Get the addresses
	rawAddrs, err := os.ReadFile("simulator/.ADDRS.json")
	if err != nil {
		log.Print("Error reading addresses")
		return nil, errors.New("Simulation failed: cannot read the addresses")
	}
	var addrs map[string]string
	if err = json.Unmarshal(rawAddrs, &addrs); err != nil {
		log.Print("Error marhsaling addresses here", err)
		return nil, errors.New("Simulation failed: marshaling")
	}
	ADDR_DREL, e1 := strconv.ParseUint(addrs["ADDR_DREL"], 16, 64)
	ADDR_AEGO, e2 := strconv.ParseUint(addrs["ADDR_AEGO"], 16, 64)
	ADDR_VEGO, e3 := strconv.ParseUint(addrs["ADDR_VEGO"], 16, 64)
	OFFSET_STEP, e4 := strconv.ParseUint(addrs["OFFSET_STEP"], 10, 64)                   // base 10
	OFFSET_MAIN, e5 := strconv.ParseUint(addrs["OFFSET_MAIN"], 10, 64)                   // base 10
	MINOR_TO_MAJOR_RATIO, e6 := strconv.ParseUint(addrs["MINOR_TO_MAJOR_RATIO"], 10, 64) // base 10
	if e1 != nil || e2 != nil || e3 != nil || e4 != nil || e5 != nil || e6 != nil {
		log.Printf("Error converting the addresses e1=%v, e2=%v, e3=%v, e4=%v, e5=%v, e6=%v\n ", e1, e2, e3, e4, e5, e6)
		return nil, errors.New("Simulation failed: error converting the addresses")
	}

	// Set values in the spec
	if err = spec.Variables["ADDR_DREL"].Set(ADDR_DREL); err != nil {
		log.Printf("setting variable: %s", err)
		return nil, errors.New("Simulation failed: error setting value in spec")
	}
	if err = spec.Variables["ADDR_AEGO"].Set(ADDR_AEGO); err != nil {
		log.Printf("setting variable: %s", err)
		return nil, errors.New("Simulation failed: error setting value in spec")
	}
	if err = spec.Variables["ADDR_VEGO"].Set(ADDR_VEGO); err != nil {
		log.Printf("setting variable: %s", err)
		return nil, errors.New("Simulation failed: error setting value in spec")
	}
	if err = spec.Variables["MINOR_TO_MAJOR_RATIO"].Set(uint32(MINOR_TO_MAJOR_RATIO)); err != nil {
		log.Printf("setting variable: %s", err)
		return nil, errors.New("Simulation failed: error setting value in spec")
	}

	// Set the simulation number of cycles
	var MAX_CYCLES uint32
	dataPoints, ok := data["datapoints"].([]interface{})
	if ok {
		if len(dataPoints) != 2 {
			log.Print("Unrecognized datapoints size")
			return nil, errors.New("Simulation failed: unrecognized input")
		}
		numPoints, ok := dataPoints[1].(float64)
		if !ok {
			log.Print("Unrecognized datapoints content")
			return nil, errors.New("Simulation failed: unrecognized input")
		}
		MAX_CYCLES = uint32(numPoints)
		log.Printf("Found %d datapoints", MAX_CYCLES)
	} else {
		log.Print("Cannot detect the number of datapoints")
		return nil, errors.New("Simulation failed: unrecognized input")
	}
	if err = spec.Variables["MAX_CYCLES"].Set(MAX_CYCLES); err != nil {
		log.Printf("setting variable: %s", err)
		return nil, errors.New("Simulation failed: error setting value in spec")
	}

	// fix the spec for the the maps
	dRelMapSpec, ok := spec.Maps["d_rel_map"]
	if !ok {
		log.Print("Cannot get the d_rel map spec")
		return nil, errors.New("Simulation failed: cannot find map in spec")
	}
	dRelMapSpec.MaxEntries = MAX_CYCLES
	aEgoMapSpec, ok := spec.Maps["a_ego_map"]
	if !ok {
		log.Print("Cannot get the a_ego map spec")
		return nil, errors.New("Simulation failed: cannot find map in spec")
	}
	aEgoMapSpec.MaxEntries = MAX_CYCLES
	vEgoMapSpec, ok := spec.Maps["v_ego_map"]
	if !ok {
		log.Print("Cannot get the d_rel map spec")
		return nil, errors.New("Simulation failed: cannot find map in spec")
	}
	vEgoMapSpec.MaxEntries = MAX_CYCLES

	// load eBPF objects (maps + programs) into the kernel
	probeObjs := probeObjects{}
	if err := spec.LoadAndAssign(&probeObjs, nil); err != nil {
		log.Printf("Cannot load eBPF objects, err: %v", err)
		return nil, errors.New("Simulation failed: cannot load eBPF objects")
	}
	defer probeObjs.Close()

	// Inject datapoints (with batch update)
	keys := make([]uint32, MAX_CYCLES)
	var tmpKey uint32 = 0
	for tmpKey < MAX_CYCLES {
		keys[tmpKey] = tmpKey
		tmpKey += 1
	}
	values, err := getDRel(data, MAX_CYCLES)
	if err != nil {
		return nil, errors.New("Simulation failed: cannot convert d_rel data points")
	}
	if VERBOSE {
		log.Println("d_rel values:", values)
	}
	// Perform batch update
	_, err = probeObjs.D_relMap.BatchUpdate(keys, values, &ebpf.BatchOptions{
		Flags: uint64(ebpf.UpdateAny),
	})
	if err != nil {
		return nil, errors.New("Simulation failed: cannot perform batch update for d_rel")
	}

	// Open executable and link the uproble
	ex, err := link.OpenExecutable(binPath)
	if err != nil {
		log.Fatalf("opening executable: %s", err)
		return nil, errors.New("Simulation failed: cannot open executable")
	}
	// Link the step() uprobe
	uprobe_step, err := ex.Uprobe(symbol, probeObjs.UprobeDrelProbe, &link.UprobeOptions{Offset: OFFSET_STEP})
	if err != nil {
		log.Fatal("cannot set the uprobe to step()")
		return nil, errors.New("Simulation failed: cannot attach to step()")
	}
	defer uprobe_step.Close()
	// Link the main() uprobe
	uprobe_main, err := ex.Uprobe(symbol, probeObjs.UprobeOutputProbe, &link.UprobeOptions{Offset: OFFSET_MAIN})
	if err != nil {
		log.Fatal("cannot set the uprobe to main()")
		return nil, errors.New("Simulation failed: cannot attach to main()")
	}
	defer uprobe_main.Close()

	// Run the simulation and wait until it terminates
	binCmd := exec.Command(binPath)
	binCmd.Stdout = os.Stdout
	binCmd.Stderr = os.Stderr
	log.Println("Starting simulation")
	err = binCmd.Run()
	if err != nil {
		log.Printf("Simulation ended (%s)", err)
	}

	// Read the simulation output trace
	// todo
	a_ego := make([]float64, MAX_CYCLES)
	for pos := uint32(0); pos < MAX_CYCLES; pos++ {
		err := probeObjs.A_egoMap.Lookup(&pos, &a_ego[pos])
		if err != nil {
			log.Printf("a_ego: lookup failed: %v\n", err)
			return nil, errors.New("Error reading simulation results: cannot complete reads")
		}
	}
	v_ego := make([]float64, MAX_CYCLES)
	for pos := uint32(0); pos < MAX_CYCLES; pos++ {
		err := probeObjs.V_egoMap.Lookup(&pos, &v_ego[pos])
		if err != nil {
			log.Printf("v_ego: lookup failed: %v\n", err)
			return nil, errors.New("Error reading simulation results: cannot complete reads")
		}
	}

	// Return the output trace back to the server
	result := Result{
		AEgo: a_ego,
		VEgo: v_ego,
	}
	return &result, nil
}

// Extract d_rel values from the simulation raw data
func getDRel(data map[string]interface{}, dataPoints uint32) ([]float64, error) {

	values := make([]float64, dataPoints)
	rawVect, ok := data["d_rel"].([]interface{})
	if ok {
		log.Printf("Found %T datapoints", rawVect)
		for pos, rawVal := range rawVect {
			floatVal, ok := rawVal.(float64)
			if !ok {
				return nil, errors.New("Cannot convert value to float64")
			}
			values[pos] = floatVal
		}
	} else {
		log.Print("Cannot extract the d_rel values")
		return nil, errors.New("Cannot find d_rel in map")
	}
	return values, nil
}
