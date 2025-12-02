.PHONY: monitoring1
monitoring1:
	cp ../simulator/1_config.json ../simulator/config.json
	python3 monitoring.py 127.0.0.1

.PHONY: monitoring2
monitoring2:
	cp ../simulator/2_config.json ../simulator/config.json
	python3 monitoring.py 127.0.0.1

.PHONY: falsification1
falsification1:
	cp ../simulator/1_config.json ../simulator/config.json
	python3 falsification.py 127.0.0.1

.PHONY: signpert2
signpert2:
	cp ../simulator/2_config.json ../simulator/config.json
	python3 sign_perturbation.py 127.0.0.1
