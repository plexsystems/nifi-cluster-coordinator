files = py_example test *.py
test_files = *

test:
	pytest -s -v test/test_$(test_files).py --doctest-modules --cov py_example --cov-config=.coveragerc --cov-report term-missing

lint:
	flake8 $(files)

fix:
	autopep8 --in-place -r $(files)

install:
	pip install -U -r requirements.txt -r test-requirements.txt

report:
	codecov

.PHONY: test lint fix install report
