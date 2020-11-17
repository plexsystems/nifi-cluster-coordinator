import logging
import requests
import utils.url_helper as url_helper
from configuration.cluster import Cluster
from configuration.project import Project, ProjectCluster, ProjectEnvironment
from configuration.parameter_context import ParameterContext


def sync(cluster: Cluster, project: Project, project_cluster: ProjectCluster, parameter_contexts: list):
    logger = logging.getLogger(__name__)

    desired_environments = list(filter(lambda e: e.is_coordinated, project_cluster.environments))

    logger.info(f'Collecting currently configured environments for project: {project.name}')
    response = requests.get(
        **cluster._get_connection_details(
            '/' + url_helper.construct_path_parts(['process-groups', project_cluster.project_process_group_id, 'process-groups']))).json()
    current_environments_json_dict = {project['component']['name']: project for project in response['processGroups']}

    for delete_env_name in list(filter(lambda k: len([p for p in project_cluster.environments if p.name.lower() == k.lower()]) == 0, current_environments_json_dict.keys())):
        _delete(cluster, project, current_environments_json_dict[delete_env_name])

    for environment in desired_environments:
        if environment.name in current_environments_json_dict:
            _update(cluster, project, project_cluster, environment, current_environments_json_dict[environment.name], parameter_contexts)
        else:
            _create(cluster, project, project_cluster, environment, parameter_contexts)

    uncoordinated_environments = list(filter(lambda e: not e.is_coordinated, project_cluster.environments))
    for environment in uncoordinated_environments:
        if environment.name in current_environments_json_dict:
            environment.process_group_id = current_environments_json_dict[environment.name]['id']


def _create(
    cluster: Cluster,
    project: Project,
    project_cluster: ProjectCluster,
    environment: ProjectEnvironment,
    parameter_contexts: list
):
    logger = logging.getLogger(__name__)

    desired_version = _get_desired_version(project, environment)
    if desired_version is None:
        logger.warning(
            f'Unable to find project version: {environment.version}, for project: {project.name}, environment: {environment.name}.')
        return

    project_cluster = project.get_project_cluster(cluster)
    if project_cluster is None:
        logger.info(f'No cluster configuration found for project: {project.name}')
        return

    post_url = '/' + url_helper.construct_path_parts(['process-groups', project_cluster.project_process_group_id, 'process-groups'])
    create_json = {
        'revision': {
            'version': 0
        },
        'component': {
            'name': environment.name,
            'comments': environment.description,
        }
    }

    if environment.parameter_context_name:
        parameter_context = _get_parameter_context_by_name(environment.parameter_context_name, parameter_contexts)
        if parameter_context is None or parameter_context.id is None:
            logger.warning(f'Unable to find parameter context: {environment.parameter_context_name}, for project: {project.name}, environment: {environment.name}.')
            return
        create_json['component']['parameterContext'] = {
            'id': parameter_context.id,
            'component': {
                'id': parameter_context.id,
                'name': environment.parameter_context_name
            }
        }

    try:
        response = requests.post(**cluster._get_connection_details(post_url), json=create_json)
        if response.status_code != 201:
            logger.warning(response.text)
            return

        response_json = response.json()
        environment.process_group_id = response_json['id']
        logger.info(f'Created project: {project.name}, environment: {environment.name}, in cluster: {cluster.name}.')
        _update(cluster, project, project_cluster, environment, response_json, parameter_contexts)
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to create project: {project.name}, environment: {environment.name}, in cluster: {cluster.name}.')
        logger.warning(exception)


def _update(
    cluster: Cluster,
    project: Project,
    project_cluster: ProjectCluster,
    environment: ProjectEnvironment,
    environment_json,
    parameter_contexts: list
):
    logger = logging.getLogger(__name__)

    environment.process_group_id = environment_json['id']

    desired_version = _get_desired_version(project, environment)
    if desired_version is None:
        logger.warning(
            f'Unable to find project version: {environment.version}, for project: {project.name}, environment: {environment.name}, in cluster: {cluster.name}.')
        return

    update_version = True
    if (
        'versionControlInformation' in environment_json['component']
        and desired_version == environment_json['component']['versionControlInformation']['version']
    ):
        update_version = False

    if (
        environment.name.lower() != environment_json['component']['name'].lower()
        # Temporarily commented: comments get overridden by versioned flow, nifi may have an issue here
        # or environment.description.lower() != environment_json['component']['comments'].lower()
        or (environment.parameter_context_name and not('parameterContext' in environment_json['component']))
        or (not environment.parameter_context_name and 'parameterContext' in environment_json['component'])
        or (
            environment.parameter_context_name
            and 'parameterContext' in environment_json['component']
            and environment.parameter_context_name.lower() != environment_json['component']['parameterContext']['component']['name'].lower()
        )

    ):
        environment_json['component']['name'] = environment.name
        environment_json['component']['comments'] = environment.description

        if 'parameterContext' in environment_json['component']:
            del environment_json['component']['parameterContext']

        if environment.parameter_context_name:
            parameter_context = _get_parameter_context_by_name(environment.parameter_context_name, parameter_contexts)
            if parameter_context is None or parameter_context.id is None:
                logger.warning(f'Unable to find parameter context: {environment.parameter_context_name}, for project: {project.name}, environment: {environment.name}, in cluster: {cluster.name}.')
                return
            environment_json['component']['parameterContext'] = {
                'id': parameter_context.id,
                'component': {
                    'id': parameter_context.id,
                    'name': environment.parameter_context_name
                }
            }

        # remove version control to update
        if 'versionControlInformation' in environment_json['component']:
            try:
                delete_version_url = '/' + url_helper.construct_path_parts(['versions', 'process-groups', environment_json['id']])
                response = requests.delete(
                    **cluster._get_connection_details(delete_version_url),
                    params={'version': str(environment_json['revision']['version'])})
                if response.status_code != 200:
                    logger.warning(response.text)
                    return
                update_version = True
            except requests.exceptions.RequestException as exception:
                logger.warning(f'Unable to temporarily delete version control from project: {project.name}, environment: {environment.name}, in cluster: {cluster.name}.')
                logger.warning(exception)
                return

        try:
            put_url = '/' + url_helper.construct_path_parts(['process-groups', environment_json['id']])
            response = requests.put(**cluster._get_connection_details(put_url), json=environment_json)
            if response.status_code != 200:
                logger.warning(response.text)
                return
            logger.info(f'Updated project: {project.name}, environment: {environment.name}, in cluster: {cluster.name}.')
            environment_json = response.json()
        except requests.exceptions.RequestException as exception:
            logger.warning(f'Unable to update project: {project.name}, environment: {environment.name}, in cluster: {cluster.name}.')
            logger.warning(exception)

    elif not update_version:
        logger.info(f'Project: {project.name}, environment: {environment.name}, in cluster: {cluster.name}, is up-to-date.')

    if update_version:
        _update_version(desired_version, cluster, project, environment, environment_json)


def _delete(cluster: Cluster, project: Project, delete_environment_json):
    logger = logging.getLogger(__name__)
    environment_name = delete_environment_json['component']['name']

    delete_url = '/' + url_helper.construct_path_parts(['process-groups', delete_environment_json['component']['id']])
    try:
        response = requests.delete(
            **cluster._get_connection_details(delete_url),
            params={'version': str(delete_environment_json['revision']['version'])})
        if response.status_code != 200:
            logger.warning(response.text)
            return
        logger.info(f'Deleted project: {project.name}, environment: {environment_name}, from cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to delete project: {project.name}, environment: {environment_name}, from cluster: {cluster.name}.')
        logger.warning(exception)


def _update_version(desired_version, cluster: Cluster, project: Project, environment: ProjectEnvironment, environment_json):
    logger = logging.getLogger(__name__)

    registry_json = cluster.registeries_json_dict[project.registry_name]
    version_update_json = {
        'processGroupRevision': environment_json['revision'],
        'versionControlInformation': {
            'groupId': environment_json['id'],
            'registryId': registry_json['id'],
            'bucketId': project.bucket_id,
            'flowId': project.flow_id,
            'version': desired_version
        }
    }

    # Todo: since version control is an async process inside nifi, we need an async logic or while loop to check
    # the request status to issue delete request when the versionrequest is processed by the nifi server
    post_url = '/' + url_helper.construct_path_parts(['versions', 'update-requests', 'process-groups', environment_json['id']])
    try:
        response = requests.post(**cluster._get_connection_details(post_url), json=version_update_json)
        if response.status_code != 200:
            logger.warning(response.text)
            return
        logger.info(f'Updated project: {project.name}, environment: {environment.name}, version: {desired_version}, in cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to update project: {project.name}, environment: {environment.name}, version: {desired_version}, in cluster: {cluster.name}.')
        logger.warning(exception)


def _get_desired_version(project: Project, environment: ProjectEnvironment):
    desired_version = environment.version
    if str(desired_version).lower() == 'latest':
        return max(project.available_versions_dict.keys())
    elif desired_version in project.available_versions_dict.keys():
        return desired_version
    else:
        return None


def _get_parameter_context_by_name(name: str, parameter_contexts: list) -> ParameterContext:
    contexts = [pc for pc in parameter_contexts if pc.name.lower() == name.lower()]
    if len(contexts) == 0:
        return None
    return contexts[0]
