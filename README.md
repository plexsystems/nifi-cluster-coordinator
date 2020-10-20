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

The nifi-cluster-coordinator will ensure that the same Apache Nifi Registry entries are present on all managed clusters.

__Note__: Apache Nifi instances running in unsecured mode cannot accept Apache Nifi Registry URI's configured for https.  The nifi-cluster-coordinator will write a WARNING log when this is encountered.

```yaml
registries:
  - name: foo-registry
    host_name: 'https://foo-registry/nifi-registry'
    description: 'This is a local registry'
```

#### Project Spaces and Environments

The `projects` section of the configuration file describes each project space within the clusters coordinator manages. A project space is a process group that appears in the `root` process group of a nifi instance.

Project environments are instances of a process group inside of a `project`.

Project environments are named on a per cluster per project instance.

For example project `foo` might have three environments:

`sandbox`
`integration-testing`
`production`

The `sandbox` environment would be used by the process owner to develop and modify how a process group works.
The `sandbox` process group would be under source control with a nifi registry and changes would be committed from this environment instance.

To update the `integration-testing` and `production` environment the nifi-cluster-coordinator would own the version number each of those instances is running at and facilitate changing the version number via a rest api call.

```yaml
projects:
  - name: foo-project
    description:  'This is foo project'
    registry_name: foo-registry
    bucket_id: a7180a6a-fdaa-4d0f-bdf6-6380e2bfa1a3
    flow_id: a7180a6a-fdaa-4d0f-bdf6-6380e2bfa1a4
    clusters:
      - cluster_name: foo-cluster
        environments:
          - name: integration
            description:  'This is an integration environment'
            is_coordinated: true
            version: 3
            parameter_context_name: 'foo-parameter-context'
          - name: sandbox
            description:  'This is a sandbox environment'
            is_coordinated: false
            version: latest
            parameter_context_name: 'foo-2-parameter-context'
      - cluster_name: foo-2-cluster
        environments:
          - name: production
            description:  'This is a production environment'
            is_coordinated: true
            version: 2
            parameter_context_name: 'foo-parameter-context'
```

#### Parameter Contexts

The `parameter_contexts` section of the configuration file describes parameter contexts within clusters coordinator manages.

A `parameter-Context` is a named set of parameters defined at controller level and supplied to project environment process gorup.

```yaml
parameter_contexts:
  - name: 'foo-parameter-context'
    description: 'This is foo parameter context'
    is_coordinated: true
    parameters:
      - name: 'foo-param-1'
        description:  'This is foo 1 param 1'
        is_sensitive: false
        value: 'foo-value-1'
      - name: 'foo-param-2'
        description: 'This is foo 1 param 2'
        is_sensitive: false
        value: 'foo-value-2'
  - name: 'foo-2-parameter-context'
    description: 'This is foo 2 parameter context'
    is_coordinated: true
    parameters:
      - name: 'foo-2-param-1'
        description: 'This is foo 2 param 1'
        is_sensitive: false
        value: 'foo-2-value-1'
      - name: 'foo-2-param-2'
        description: 'This is foo 2 param 2'
        is_sensitive: false
        value: 'foo-2-value-2'
  - name: 'foo-uncoordinated-parameter-context'
    description: 'This is uncoordinated parameter context'
    is_coordinated: false
```

#### Security

The `security` section of the configuration file defines `users`, `user groups` and the ability for users and groups to view or modify NiFi resources using `access policies` within clusters coordinator manages.

There are two types of `access policies` that can be applied to a resource:

`read` if a read view policy is created for a resource, only the users or groups that are added to that policy are able to see the details of that resource.

`write` if a resource has a write or modify policy, only the users or groups that are added to that policy can change the configuration of that resource.

You can create and apply `access policies` on both `global` and `component` levels.

List of `global` access policy names:

`view the UI` (readonly)
`access the controller`
`access parameter contexts`
`query provenance` (readonly)
`access restricted components`
`access all policies`
`access users/user groups`
`retrieve site-to-site details` (readonly)
`view system diagnostics` (readonly)
`proxy user requests` (readonly)
`access counters`

List of `component` access policy names:

`view the component`
`modify the component`
`operate the component`
`view provenance`
`view the data`
`modify the data`
`view the policies`
`modify the policies`

List of `component` types that can be defined:

`nifi flow` with name `root` for applying `component` access policy to the root nifi flow
`project` with project names described in `projects` section for applying `component` access policy to project process group
`environment` with envronment names described in `projects` section in project:environment format for applying `component` access policy to project environment process group

```yaml
security:
  is_coordinated: true
  users:
    - 'foo-user'
    - 'bar-user'
  user_groups:
    - identity: 'foo-group'
      members:
        - 'foo-user'
  global_access_policies:
    - name: 'view the UI'
      action: 'read'
      users:
        - 'bar-user'
      user_groups:
        - 'foo-group'
    - name: 'access the controller'
      action: 'read'
      users:
        - 'bar-user'
      user_groups:
        - 'foo-group'
    - name: 'access the controller'
      action: 'write'
      users:
      user_groups:
        - 'foo-group'
  component_access_policies:
    - name: 'view the component'
      component_type: 'nifi flow'
      component_name: 'root'
      users:
      user_groups:
        - 'foo-group'
    - name: 'modify the component'
      component_type: 'nifi flow'
      component_name: 'root'
      users:
      user_groups:
        - 'foo-group'
    - name: 'view the component'
      component_type: 'project'
      component_name: 'foo-project'
      users:
      user_groups:
        - 'foo-group'
    - name: 'modify the component'
      component_type: 'project'
      component_name: 'foo-project'
      users:
      user_groups:
        - 'foo-group'
    - name: 'view the component'
      component_type: 'environment'
      component_name: 'foo-project:integration'
      users:
        - 'bar-user'
      user_groups:
        - 'foo-group'
    - name: 'modify the component'
      component_type: 'environment'
      component_name: 'foo-project:integration'
      users:
        - 'bar-user'
      user_groups:
        - 'foo-group'
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

For local development create a copy of the `nifi-cluster-coordinator.example.yaml` and name it `nifi-cluster-coordinator.yaml`. Update it with your cluster configurations.  The `MAKEFILE` is configured out of the box to use a configuration file in that location.

Copyright (c) 2020 Plex Systems https://www.plex.com
