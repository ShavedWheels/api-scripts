build: clean virtualenv database run

clean:
	-find . -type f -name "*.pyc" -delete

virtualenv:

	pip install -r requirements.txt

run:
	python -W ignore fb_posts.py

database:
	psql -U postgres -tc "select 1 from pg_database where datname = 'postgres'" | grep -q 1 || (psql -U postgres -c "create database postgres")

.PHONY: build clean virtualenv database run
