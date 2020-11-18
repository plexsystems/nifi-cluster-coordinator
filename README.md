# nifi-cluster-coordinator

[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/plexsystems/nifi-cluster-coordinator/blob/main/LICENSE)

[![GitHub Release](https://img.shields.io/badge/release-v0.0.2-green)](https://github.com/plexsystems/nifi-cluster-coordinator/releases)

Utility which can be used to centrally manage multiple [Apache Nifi](https://nifi.apache.org/) instances.

List of currently supported objects

* [NiFi Registry](https://nifi.apache.org/registry.html) entries
* Users & Groups
* Policies
* Parameter Contexts
* Process Groups

## The Problem

We at [Plex](https://www.plex.com) manage multiple datacenters supporting manufacturers around the globe with our Smart Manufacturing Platform.

Our analytics team leverages Apache NiFi to daily perform tens of thousands of ETL jobs for our customers to help power our reporting platforms.

The team needed a way to centrally manage the running state of these clusters, and so we created the `nifi-cluster-coordinator`.

With the `nifi-cluster-coordinator` you can manage the configuration of multiple clusters from a single location making this a perfect tool to include as part of a CI/CD or gitops process.

### Usage

The nifi-cluster-coordinator works on the idea of __desired state__ vs. __configured state__.

By giving the tool a `yaml` based configuration file the tool can insure that multiple Apache Nifi instances are configured the same.

The coordinator will do the following:

* __ADD__ Any new objects found in the configuation but not on the cluster
* __UPDATE__ Any existing objects who's configuration differs between the configuration and cluster
* __REMOVE__ Any objects found on the cluster but not in the configuation

The coordinator is very aggressive at cleanup so failure to give the coordinator the correct configuration could cause your cluster to become inaccessible (see User Pre-Requirements section).

### Command Line Arguments

The `nifi-cluster-coordinator` is a `python` program which accepts a few command line arguments

`--loglevel LEVEL` (optional)

This may be set to `DEBUG`, `INFORMATION`, `WARNING`, `CRITICAL`.  The default level is `INFORMATION`.

`--configfile /path/to/file.yaml` (required)

The location on disk of the config file that you want nifi-cluster-coordinator to read and process.

`--watch` (optional)

Leaves the application running, watching the configuration file for changes.  The application will re-apply the configuration each time the file is updated.

### Pre-Requirements

#### Cluster Coordinator User Permissions

In secured clusters, the user that the coordinator runs as needs the following permissions

Global Permissions
* View the user interface
* Access the controller __view__
* Access the controller __modify__
* Access Parameter Contexts __view__
* Access Parameter Contexts __modify__
* Access all polices __view__
* Access all policies __modify__
* Access users/user groups __view__
* Access users/user groups __modify__

Root Process Group Permissions
* View the component
* Modify the component
* View the polices
* Modify the policies

:warning: If you are running a secured NiFi instance make sure you **include** the machine user account along with the `proxy user requests` policy and `write` action for this account.  Failure to do so could render your cluster inaccessible till you manually fix your `users.xml` and `authorizations.xml` files.

### Configuration

Below is a detailed description of each of the sections inside the configuration file.

#### clusters

The `clusters` section of the configuration is an array of clusters that the cluster coordinator manages.  These instances can be both clusters or stand alone.  For the purposes of the nifi-cluster-coordinator we call them all clusters.

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
        ssl_key_file: '/foo/foo-user-key.pem'
        ssl_ca_cert: '/foo/foo-root-ca-cert.pem'
  - name: foo-2-cluser
    host_name: 'http://foo-2-cluster/nifi-api'
    security:
      use_certificate: false
```

#### registries

List of Apache Nifi Registry entries.  The coordinator will ensure that __all__ entries will be configured on __all__ managed clusters.

__Note__: Apache Nifi instances running in unsecured mode cannot accept Apache Nifi Registry URI's configured for https.  The nifi-cluster-coordinator will write a `WARNING` log entry when this is encountered.

```yaml
registries:
  - name: foo-registry
    host_name: 'https://foo-registry/nifi-registry'
    description: 'This is a local registry'
```

#### projects

`Projects` is a term the Plex team adopted to describe a process group that lives in the root process group and acts as a container for one or more instances of dedicated process groups.  We've found that this lines up with the idea that many teams may be using the same NiFi cluster and need a space to do work.  Process groups acting as a project container are __not__ under source control.

`Projects` will have one or more `environment`.  An environment is another process group but this time is a process group that __is__ under srouce control.  A process might have multple environments, for example a `dev`, `uat`, and `prod` instances each configured with different parameter contexts to point at different external resources.

Project environments are named on a per cluster per project instance.

To update the `integration-testing` and `production` environment the nifi-cluster-coordinator would own the version number each of those instances is running at and facilitate changing the version number via a rest api call.

The `is_coordinated` property can be set to `true` or `false`.  Use `is-coordinated: false` to tell the coordinator about a process group you don't want it to garbage collect, but are not using the coordinator to manage version control on.

The `version` property can be set to either `latest` or an integer number which is the NiFi Registry Version number you want present in that environment.

In the example below the `foo-cluster` is responsible for running the `sandbox` and `integration` environments for our project.  Our development team performs updates against the `sandbox` instance in NiFi.  They use a pull request against the configuration file to bump the version numbers on the `integration` and `production` environments.  In this example our integration environmet is running version 3 while production is still running version 2.

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

#### parmaeter_contexts

The `parameter_contexts` section of the configuration file describes parameter contexts within clusters coordinator manages.

Just like in the projects and environment the `is_coordinated` property is used to tell the coordinator about parameter contexts you do not want garbage collected during the coordinator cleanup phase, but are not actually managing the properties via the coordinator.

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

#### security

The `security` section of the configuration file defines `users`, `user groups` and the ability for users and groups to view or modify NiFi resources using `access policies` within clusters the coordinator manages.

There are two types of `access policies` that can be applied to a resource:

`read` if a read view policy is created for a resource, only the users or groups that are added to that policy are able to see the details of that resource.

`write` if a resource has a write or modify policy, only the users or groups that are added to that policy can change the configuration of that resource.

You can create and apply `access policies` on both `global` and `component` levels.

List of readonly `global` access policy names:

* `view the UI`
* `query provenance`
* `retrieve site-to-site details`
* `view system diagnostics`
* `proxy user requests`

List of read-write `global` access policy names:

* `access the controller`
* `access parameter contexts`
* `access restricted components`
* `access all policies`
* `access users/user groups`
* `access counters`

List of `component` access policy names:

* `view the component`
* `modify the component`
* `operate the component`
* `view provenance`
* `view the data`
* `modify the data`
* `view the policies`
* `modify the policies`

List of `component` types that can be defined:

`nifi flow` with name `root` for applying `component` access policy to the root nifi flow.

`project` with project names described in `projects` section for applying `component` access policy to project process group.

`environment` with envronment names described in `projects` section in project:environment format for applying `component` access policy to project environment process group.

Environments can accept a list of `clusters` which will only apply that policy to the provided list of clusters.  If the `clusters` list is omitted the coordinator will attempt to apply the policy to all clusters.  You will get a `WARNING` log message if the coordinator attempts to apply a component policy to a component that doest exist on the cluster.

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
      clusters:
        - foo-cluster
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
