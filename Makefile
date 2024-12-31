IMAGE_NAME ?= scrabble
IMAGE_TAG ?= latest
PORT ?= 5678


build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

run-server: build
	docker run --rm -it -p $(PORT):5678 --mount type=bind,source="$(PWD)"/__logs__,target=/tmp/scrabble/ $(IMAGE_NAME):$(IMAGE_TAG) python run_cmd.py host --port 5678 --host 0.0.0.0

run-client: build
	docker run --rm -it --network host --mount type=bind,source="$(PWD)"/__logs__,target=/tmp/scrabble/ $(IMAGE_NAME):$(IMAGE_TAG) python run_cmd.py player $(args)
