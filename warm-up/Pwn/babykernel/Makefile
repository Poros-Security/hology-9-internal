.PHONY: all assets docker handout clean

all: assets

assets:
	./build/build-local-artifacts.sh

docker:
	docker build -t hibchb26/babykernel:latest .

handout:
	./build/build-handout.sh

clean:
	$(MAKE) -C src clean || true
	rm -rf dist
