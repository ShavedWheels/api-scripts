build: clean virtualenv

clean:
	-find . -type f -name "*.pyc" -delete

virtualenv:


	pip install -r requirements.txt

.PHONY: build clean virtualenv
