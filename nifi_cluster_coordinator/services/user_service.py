import logging
import requests
import utils.url_helper as url_helper
from configuration.cluster import Cluster
from configuration.security import User


def sync(cluster: Cluster, configured_users: list):
    """Set the cluster users to desired configuration."""
    logger = logging.getLogger(__name__)

    logger.info(f'Getting coordinator user for cluster: {cluster.name}')
    response = requests.get(
        **cluster._get_connection_details(
            '/' + url_helper.construct_path_parts(['flow', 'current-user']))).json()
    current_user_identity = response['identity']

    desired_users = configured_users
    if len([u for u in desired_users if u.identity.lower() == current_user_identity.lower()]) == 0:
        desired_users.append(User(current_user_identity))

    logger.info(f'Collecting currently configured users for cluster: {cluster.name}')
    response = requests.get(
        **cluster._get_connection_details(
            '/' + url_helper.construct_path_parts(['tenants', 'users']))).json()
    current_users_json_dict = {user['component']['identity']: user for user in response['users']}

    for delete_user_name in list(
        filter(
            lambda k: current_user_identity.lower() != k.lower() and len([
                u for u in desired_users if u.identity.lower() == k.lower()
            ]) == 0, current_users_json_dict.keys())):
        _delete(cluster, current_users_json_dict[delete_user_name])

    for user in desired_users:
        if user.identity in current_users_json_dict:
            _update(cluster, user, current_users_json_dict[user.identity])
        else:
            _create(cluster, user)


def _create(cluster: Cluster, user: User):
    logger = logging.getLogger(__name__)

    create_json = {
        'revision': {
            'version': 0
        },
        'component': {
            'identity': user.identity
        }
    }

    try:
        response = requests.post(
            **cluster._get_connection_details(
                '/' + url_helper.construct_path_parts(['tenants', 'users'])), json=create_json)
        if response.status_code != 201:
            logger.warning(f'Unable to create user: {user.identity}, in cluster: {cluster.name}.')
            logger.warning(response.text)
            return

        user.component_id = response.json()['id']
        logger.info(f'Created user: {user.identity}, in cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to create user: {user.identity}, cluster: {cluster.name}.')
        logger.warning(exception)


def _update(cluster: Cluster, user: User, current_user_json):
    logger = logging.getLogger(__name__)

    user.component_id = current_user_json['id']
    logger.info(f'User: {user.identity}, in cluster: {cluster.name}, already exists.')


def _delete(cluster: Cluster, delete_user_json):
    logger = logging.getLogger(__name__)
    user_identity = delete_user_json['component']['identity']

    delete_url = '/' + url_helper.construct_path_parts(['tenants', 'users', delete_user_json['id']])
    try:
        response = requests.delete(
            **cluster._get_connection_details(delete_url),
            params={'version': str(delete_user_json['revision']['version'])})
        if response.status_code != 200:
            logger.warning(f'Unable to delete user: {user_identity}, from cluster: {cluster.name}.')
            logger.warning(response.text)
            return
        logger.info(f'Deleted user: {user_identity}, from cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to delete user: {user_identity}, from cluster: {cluster.name}.')
        logger.warning(exception)
