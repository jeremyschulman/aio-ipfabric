PACKAGE_and_VERSION = $(shell poetry version)
PACKAGE_NAME = "aioipfabric"
PACKAGE_VERSION = $(word 2, $(PACKAGE_and_VERSION))

all: precheck

.PHONY: precheck
precheck:
	black $(PACKAGE_NAME)
	pre-commit run -a
	interrogate -c pyproject.toml


.PHONY: build
build: setup.py requirements.txt

setup.py:
	poetry build && \
	tar --strip-components=1 -xvf dist/$(DIST_BASENAME).tar.gz '*/setup.py'

requirements.txt:
	poetry export --without-hashes > requirements.txt

clean:
	rm -rf dist *.egg-info .pytest_cache
	rm -f requirements.txt setup.py
	rm -f poetry.lock

