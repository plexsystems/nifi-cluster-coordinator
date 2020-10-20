from .cluster import Cluster


class ProjectEnvironment:

    def __init__(self, name, description, is_coordinated, version, parameter_context_name):
        self.name = name
        self.description = description
        self.is_coordinated = is_coordinated
        self.version = version
        self.parameter_context_name = parameter_context_name
        self.process_group_id = ''


class ProjectCluster:

    def __init__(self, name, environments):
        self.name = name
        self.environments = [
            ProjectEnvironment(
                name=e['name'],
                description=e['description'],
                is_coordinated=e['is_coordinated'],
                version=e['version'],
                parameter_context_name=e['parameter_context_name'])
            for e in environments
        ]
        self.project_process_group_id = ''


class Project:

    def __init__(self, name, description, registry_name, bucket_id, flow_id, clusters):
        self.name = name
        self.description = description
        self.registry_name = registry_name
        self.bucket_id = bucket_id
        self.flow_id = flow_id
        self.clusters = [ProjectCluster(name=c['cluster_name'], environments=c['environments']) for c in clusters]
        self.available_versions_dict = None

    def get_project_cluster(self, cluster: Cluster) -> ProjectCluster:
        clusters = [c for c in self.clusters if c.name.lower() == cluster.name.lower()]
        if len(clusters) == 0:
            return None
        return clusters[0]
