.PHONY: test lint fix install report

project_folder = src
test_folder = test
files = $(project_folder)/*.py $(test_folder)/*.py
test_files = test_*.py

test:
	pytest -s -v $(test_folder)/$(test_files) --doctest-modules --cov $(project_folder) --cov-config=.coveragerc --cov-report term-missing

lint:
	flake8 $(files)

fix:
	autopep8 --in-place -r $(files)

install:
	pip3 install -U -r requirements.txt