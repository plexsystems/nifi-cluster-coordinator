# nifi-cluster-coordinator

This is a work in progress project which can be used to coordinate deploying the same Apache NiFi process group version to multiple clusters.

This is useful for people who need to maintain the same version of a flow on separate clusters for CI/CD and multiple data center purposes.

## Getting Started

The following packages need to be available on your system as they are required for the [nipyapi](https://nipyapi.readthedocs.io/en/latest/) package.

- `libxml2-dev`
- `libxslt-dev`

Create a python virtual environment.

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Run `make dev-setup`.

## Configuration

Create a copy of the `nifi-cluster-coordinator.example.yaml` and name it `nifi-cluster-coordinator.yaml` and update it with your cluster configurations.

Copyright (c) 2020 Plex Systems https://www.plex.com