import logging
import requests
import utils.url_helper as url_helper
from configuration.cluster import Cluster
from configuration.parameter_context import ParameterContext


def sync(cluster: Cluster, configured_parameter_contexts: list):
    """Set the cluster parameter contexts to desired configuration."""
    logger = logging.getLogger(__name__)

    desired_parameter_contexts = list(filter(lambda pc: pc.is_coordinated, configured_parameter_contexts))

    logger.info(f'Collecting currently configure parameter contexts for cluster: {cluster.name}')
    response = requests.get(
        **cluster._get_connection_details(
            '/' + url_helper.construct_path_parts(['flow', 'parameter-contexts']))).json()
    current_parameter_contexts_json_dict = {context['component']['name']: context for context in response['parameterContexts']}

    for delete_parameter_context_name in list(filter(lambda k: len([pc for pc in configured_parameter_contexts if pc.name.lower() == k.lower()]) == 0, current_parameter_contexts_json_dict.keys())):
        _delete(cluster, current_parameter_contexts_json_dict[delete_parameter_context_name])

    for parameter_context in desired_parameter_contexts:
        if parameter_context.name in current_parameter_contexts_json_dict:
            _update(cluster, parameter_context, current_parameter_contexts_json_dict[parameter_context.name])
        else:
            _create(cluster, parameter_context)

    uncoordinated_parameter_contexts = list(filter(lambda pc: not pc.is_coordinated, configured_parameter_contexts))
    for parameter_context in uncoordinated_parameter_contexts:
        if parameter_context.name in current_parameter_contexts_json_dict:
            parameter_context.id = current_parameter_contexts_json_dict[parameter_context.name]['id']
        else:
            parameter_context.id = None


def _create(cluster: Cluster, parameter_context: ParameterContext):
    logger = logging.getLogger(__name__)

    create_json = {
        'revision': {
            'version': 0
        },
        'component': {
            'name': parameter_context.name,
            'description': parameter_context.description,
            'parameters': []
        }
    }

    for parameter in parameter_context.parameters:
        create_json['component']['parameters'].append({
            'parameter': {
                'name': parameter.name,
                'description': parameter.description,
                'sensitive': parameter.is_sensitive,
                'value': parameter.value
            }
        })

    try:
        response = requests.post(**cluster._get_connection_details('/parameter-contexts'), json=create_json)
        if response.status_code != 201:
            logger.warning(f'Unable to create parameter context: {parameter_context.name}, in cluster: {cluster.name}.')
            logger.warning(response.text)
            return
        parameter_context.id = response.json()['id']
        logger.info(f'Created parameter context: {parameter_context.name}, in cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to create parameter context: {parameter_context.name}, cluster: {cluster.name}.')
        logger.warning(exception)


def _update(cluster: Cluster, parameter_context: ParameterContext, current_parameter_context_json):
    logger = logging.getLogger(__name__)

    parameter_context.id = current_parameter_context_json['id']

    if (
        parameter_context.description.lower() != current_parameter_context_json['component']['description'].lower()
        or _did_parameters_change(parameter_context, current_parameter_context_json)
    ):
        url = '/' + url_helper.construct_path_parts(['parameter-contexts', parameter_context.id, 'update-requests'])
        current_parameter_context_json['component']['description'] = parameter_context.description
        current_parameter_context_json['component']['parameters'] = []

        for parameter in parameter_context.parameters:
            current_parameter_context_json['component']['parameters'].append({
                'parameter': {
                    'name': parameter.name,
                    'description': parameter.description,
                    'sensitive': parameter.is_sensitive,
                    'value': parameter.value
                }
            })

        try:
            response = requests.post(**cluster._get_connection_details(url), json=current_parameter_context_json)
            if response.status_code != 200:
                logger.warning(response.text)
                return
            logger.info(f'Updated parameter context: {parameter_context.name}, in cluster: {cluster.name}.')
        except requests.exceptions.RequestException as exception:
            logger.warning(f'Unable to update parameter context: {parameter_context.name}, in cluster: {cluster.name}.')
            logger.warning(exception)

    else:
        logger.info(f'Parameter context: {parameter_context.name}, in cluster: {cluster.name}, is up-to-date.')


def _delete(cluster: Cluster, delete_parameter_context_json):
    logger = logging.getLogger(__name__)
    parameter_context_name = delete_parameter_context_json['component']['name']

    delete_url = '/' + url_helper.construct_path_parts(['parameter-contexts', delete_parameter_context_json['component']['id']])
    try:
        response = requests.delete(
            **cluster._get_connection_details(delete_url),
            params={'version': str(delete_parameter_context_json['revision']['version'])})
        if response.status_code != 200:
            logger.warning(f'Unable to delete parameter context: {parameter_context_name}, from cluster: {cluster.name}.')
            logger.warning(response.text)
            return
        logger.info(f'Deleted parameter context: {parameter_context_name}, from cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to delete parameter context: {parameter_context_name}, from cluster: {cluster.name}.')
        logger.warning(exception)


def _did_parameters_change(parameter_context: ParameterContext, current_parameter_context_json):
    if len(parameter_context.parameters) != len(current_parameter_context_json['component']['parameters']):
        return True

    for parameter in parameter_context.parameters:
        parameters = [
            p for p in current_parameter_context_json['component']['parameters']
            if p['parameter']['name'].lower() == parameter.name.lower()
            and p['parameter']['description'].lower() == parameter.description.lower()
            and p['parameter']['sensitive'] == parameter.is_sensitive
            and str(p['parameter']['value']).lower() == str(parameter.value).lower()
        ]

        if len(parameters) == 0:
            return True

    return False
