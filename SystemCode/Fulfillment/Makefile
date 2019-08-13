.PHONY: clean run migrate refresh

TEST_PATH=./

help:
	@echo "    run"
	@echo "    	   Runs the chatbot backend
	@echo "    ngrok
	@echo "    	   Runs ngrok

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf docs/_build

run:
	python TouristFood-main.py

ngrok:
	ngrok http 5000
