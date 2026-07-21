.PHONY: format, install

format:
	black . --line-length=120

install:
	pip install -r requirements.txt
