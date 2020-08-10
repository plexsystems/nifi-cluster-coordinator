.PHONY: test lint fix install build

project_folder = nifi_cluster_coordinator
test_folder = test
entry_file = main.py
files = $(wildcard **/*.py)
test_files = $(wildcard **/test_*.py)
config_file = conf/nifi-cluster-coordinator.yaml
default_log_level = DEBUG

run: fix
	@python3 $(project_folder)/$(entry_file) --loglevel $(default_log_level) --configfile $(config_file)

test:
	@pytest -s -v $(test_files) --doctest-modules --cov $(project_folder) --cov-config=.coveragerc --cov-report term-missing

# Ignoring W292 on linting because autopep8 can't seem to fix it
lint:
	@flake8 --statistics --extend-ignore=W292,W503 $(project_folder) $(test_folder)

fix:
	@autopep8 --aggressive --in-place -r $(project_folder) $(test_folder)

dev-setup:
	@pip3 install -U -r requirements.txt

build: lint clean
	@docker build . -t nifi-cluster-coordinator:$(dockertag)

clean:
	@find . -name '*.pyc' -exec rm --force {} +