import logging
import requests
import utils.url_helper as url_helper
import services.environment_service as environment_service
from configuration.cluster import Cluster
from configuration.project import Project


def sync(cluster: Cluster, configured_projects: list, parameter_contexts: list):
    """Set the cluster projects to their desired configuration."""
    logger = logging.getLogger(__name__)

    desired_projects = list(filter(lambda p: len([c for c in p.clusters if c.name.lower() == cluster.name.lower()]) > 0, configured_projects))

    logger.info(f'Collecting currently configure projects for cluster: {cluster.name}')
    response = requests.get(
        **cluster._get_connection_details(
            '/' + url_helper.construct_path_parts(['process-groups', cluster.root_process_group_id, 'process-groups']))).json()
    current_projects_json_dict = {project['component']['name']: project for project in response['processGroups']}

    for delete_project_name in list(filter(lambda k: len([p for p in desired_projects if p.name.lower() == k.lower()]) == 0, current_projects_json_dict.keys())):
        _delete(cluster, current_projects_json_dict[delete_project_name])

    for desired_project in desired_projects:
        if desired_project.name in current_projects_json_dict:
            _update(cluster, desired_project, current_projects_json_dict[desired_project.name], parameter_contexts)
        else:
            _create(cluster, desired_project, parameter_contexts)


def _create(cluster: Cluster, project: Project, parameter_contexts: list):
    logger = logging.getLogger(__name__)

    project_cluster = project.get_project_cluster(cluster)
    if project_cluster is None:
        logger.info(f'No cluster configuration found for project: {project.name}')
        return

    post_url = '/' + url_helper.construct_path_parts(['process-groups', cluster.root_process_group_id, 'process-groups'])
    create_json = {
        'revision': {
            'version': 0
        },
        'component': {
            'name': project.name,
            'comments': project.description
        }
    }

    try:
        response = requests.post(**cluster._get_connection_details(post_url), json=create_json)
        if response.status_code != 201:
            logger.warning(response.text)
            return
        project_cluster.project_process_group_id = response.json()['id']
        logger.info(f'Created project: {project.name}, in cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to create project: {project.name}, in cluster: {cluster.name}.')
        logger.warning(exception)
        return

    _get_available_versions(cluster, project)
    environment_service.sync(cluster, project, project_cluster, parameter_contexts)


def _update(cluster: Cluster, project: Project, current_project_json, parameter_contexts: list):
    logger = logging.getLogger(__name__)

    project_cluster = project.get_project_cluster(cluster)
    if project_cluster is None:
        logger.warning(f'No cluster configuration found for project: {project.name}')
        return

    project_cluster.project_process_group_id = current_project_json['id']

    if project.description.lower() != current_project_json['component']['comments'].lower():
        put_url = '/' + url_helper.construct_path_parts(['process-groups', project_cluster.project_process_group_id])
        current_project_json['component']['comments'] = project.description
        try:
            response = requests.put(**cluster._get_connection_details(put_url), json=current_project_json)
            if response.status_code != 200:
                logger.warning(response.text)
                return
            logger.info(f'Updated project: {project.name}, in cluster: {cluster.name}, with new description: {project.description}.')
        except requests.exceptions.RequestException as exception:
            logger.warning(f'Unable to update project: {project.name}, in cluster: {cluster.name}.')
            logger.warning(exception)
            return

    else:
        logger.info(f'Project: {project.name}, in cluster: {cluster.name}, is up-to-date.')

    _get_available_versions(cluster, project)
    environment_service.sync(cluster, project, project_cluster, parameter_contexts)


def _delete(cluster: Cluster, delete_project_json):
    logger = logging.getLogger(__name__)
    project_name = delete_project_json['component']['name']

    delete_url = '/' + url_helper.construct_path_parts(['process-groups', delete_project_json['component']['id']])
    try:
        response = requests.delete(
            **cluster._get_connection_details(delete_url),
            params={'version': str(delete_project_json['revision']['version'])})
        if response.status_code != 200:
            logger.warning(response.text)
            return
        logger.info(f'Deleted project: {project_name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to delete project: {project_name}, will try again later.')
        logger.warning(exception)


def _get_available_versions(cluster: Cluster, project: Project):
    logger = logging.getLogger(__name__)

    if not(project.registry_name in cluster.registeries_json_dict):
        logger.warning(f'Unable to find registry: {project.registry_name}, in cluster: {cluster.name}.')
        return

    registry_json = cluster.registeries_json_dict[project.registry_name]
    url = '/' + url_helper.construct_path_parts(['flow', 'registries', registry_json['id'], 'buckets', project.bucket_id, 'flows', project.flow_id, 'versions'])

    try:
        response = requests.get(**cluster._get_connection_details(url))
        if response.status_code != 200:
            logger.info(f'Unable to get flow versions for project: {project.name}, Response: {response.text}')
            return
        project.available_versions_dict = {version['versionedFlowSnapshotMetadata']['version']: version for version in response.json()['versionedFlowSnapshotMetadataSet']}
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to get flow versions for project: {project.name}.')
        logger.warning(exception)