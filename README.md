# nifi-cluster-coordinator

This is a work in progress project which can be used to coordinate deploying the same Apache NiFi process group version to multiple clusters.

This is useful for people who need to maintain the same version of a flow on separate clusters for CI/CD and multiple data center purposes.

## Getting Started

The following packages need to be available on your system

- `libxml2-dev`
- `libxslt-dev`

Create a python virtual environment.

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Run `make dev-setup`.