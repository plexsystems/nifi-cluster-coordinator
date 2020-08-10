# nifi-cluster-coordinator

This is a work in progress project which can be used to coordinate deploying the same Apache NiFi process group version to multiple clusters.

This is useful for people who need to maintain the same version of a flow on separate clusters for CI/CD and multiple data center purposes.

## Usage

The nifi-cluster-coordinator works on the idea of __desired state__ vs. __configured state__.

By giving the tool a `yaml` based configuration file the tool can insure that multiple Apache Nifi instances are configured the same.

### Arguments

`--loglevel LEVEL` (optional)

This may be set to DEBUG, INFORMATION, WARNING, CRITICAL.  The default level is INFORMATION.

`--configfile /path/to/file.yaml` (required)

The location on disk of the config file that you want nifi-cluster-coordinator to read and process.

`--watch` (optional)

Leaves the application running watching the configuration file for changes.  Useful in situations where the yaml configuration is under source control and being delivered to the tool via a CI/CD pipeline.

### Configuration

#### Clusters

The `clusters` section of the configuration file describes each Apache NiFi instance the cluster coordinator manages.  These instances can be both clusters or stand alone.  For the purposes of the nifi-cluster-coordinator we call them all clusters.

Currently the nifi-cluster-coordinator supports unsecured clusters and clusters secured via certificates.

For secured instances, the certificates required to connect to the cluster need to be accessible by the nifi-cluster-coordinator.

```yaml
clusters:
  - name: foo-cluster
    host_name: 'https://foo-cluster/nifi-api'
    security:
      use_certificate: true
      certificate_config:
        ssl_cert_file: '/foo/foo-user-cert.pem'
        ssl_ca_cert: '/foo/foo-root-ca-cert.pem'
        ssl_key_file: '/foo/foo-root-ca-key.pem'
  - name: foo-2-cluser
    host_name: 'http://foo-2-cluster/nifi-api'
    security:
      use_certificate: false
```

#### Apache NiFi Registry

The nifi-cluster-coordinator will insure that the same Apache Nifi Registry entries are present on all managed clusters.

__Note__: Apache Nifi instances running in unsecured mode cannot accept Apache Nifi Registry URI's configured for https.  The nifi-cluster-coordinator will write a WARNING log when this is encountered.

```yaml
registries:
  - name: foo-registry
    host_name: 'https://foo-registry/nifi-registry'
    description: 'This is a local registry'
```

## Developing

If you are interested in helping to develop this application follow these steps.

### Getting Started

Create a python virtual environment.

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Run `make dev-setup`.

### Configuration

For local development create a copy of the `nifi-cluster-coordinator.example.yaml` and name it `nifi-cluster-coordinator.yaml` and update it with your cluster configurations.  The `MAKEFILE` is configured out of the box to use a configuration file in that location.

Copyright (c) 2020 Plex Systems https://www.plex.com
