import logging
import requests
import utils.url_helper as url_helper
from configuration.cluster import Cluster
from configuration.security import UserGroup


def sync(cluster: Cluster, configured_user_groups: list, configured_users: list):
    """Set the cluster user groups to desired configuration."""
    logger = logging.getLogger(__name__)

    desired_users_groups = configured_user_groups

    logger.info(f'Collecting currently configured user groups for cluster: {cluster.name}')
    response = requests.get(
        **cluster._get_connection_details(
            '/' + url_helper.construct_path_parts(['tenants', 'user-groups']))).json()
    current_user_groups_json_dict = {ug['component']['identity']: ug for ug in response['userGroups']}

    for delete_user_name in list(
        filter(
            lambda k: len([
                u for u in desired_users_groups if u.identity.lower() == k.lower()
            ]) == 0, current_user_groups_json_dict.keys())):
        _delete(cluster, current_user_groups_json_dict[delete_user_name])

    for user_group in desired_users_groups:
        if user_group.identity in current_user_groups_json_dict:
            _update(cluster, user_group, current_user_groups_json_dict[user_group.identity], configured_users)
        else:
            _create(cluster, user_group, configured_users)


def _create(cluster: Cluster, user_group: UserGroup, configured_users: list):
    logger = logging.getLogger(__name__)

    create_json = {
        'revision': {
            'version': 0
        },
        'component': {
            'identity': user_group.identity,
            'users': []
        }
    }

    for user_identity in user_group.members:
        users = [u for u in configured_users if u.identity.lower() == user_identity.lower()]
        if len(users) > 0:
            create_json['component']['users'].append({
                'revision': {
                    'version': 0
                },
                'id': users[0].component_id,
                'component': {
                    'identity': user_identity,
                    'id': users[0].component_id
                }
            })
        else:
            logger.warning(f'User: {user_identity} not found in configured users.')

    try:
        response = requests.post(
            **cluster._get_connection_details(
                '/' + url_helper.construct_path_parts(['tenants', 'user-groups'])), json=create_json)
        if response.status_code != 201:
            logger.warning(f'Unable to create user group: {user_group.identity}, in cluster: {cluster.name}.')
            logger.warning(response.text)
            return

        user_group.component_id = response.json()['id']
        logger.info(f'Created user group: {user_group.identity}, in cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to create user group: {user_group.identity}, cluster: {cluster.name}.')
        logger.warning(exception)


def _update(cluster: Cluster, user_group: UserGroup, current_user_group_json, configured_users: list):
    logger = logging.getLogger(__name__)

    user_group.component_id = current_user_group_json['id']

    if _did_members_change(user_group, current_user_group_json):
        url = '/' + url_helper.construct_path_parts(['tenants', 'user-groups', current_user_group_json['id']])
        current_user_group_json['component']['users'] = []

        for user_identity in user_group.members:
            users = [u for u in configured_users if u.identity.lower() == user_identity.lower()]
            if len(users) > 0:
                current_user_group_json['component']['users'].append({
                    'revision': {
                        'version': 0
                    },
                    'id': users[0].component_id,
                    'component': {
                        'identity': user_identity,
                        'id': users[0].component_id
                    }
                })
            else:
                logger.warning(f'User: {user_identity} not found in configured users.')

        try:
            response = requests.put(**cluster._get_connection_details(url), json=current_user_group_json)
            if response.status_code != 200:
                logger.warning(f'Unable to update members for user group: {user_group.identity}, in cluster: {cluster.name}.')
                logger.warning(response.text)
                return
            logger.info(f'Updated members for user group: {user_group.identity}, in cluster: {cluster.name}.')
        except requests.exceptions.RequestException as exception:
            logger.warning(f'Unable to update members for user group: {user_group.identity}, in cluster: {cluster.name}.')
            logger.warning(exception)

    else:
        logger.info(f'Members for user group: {user_group.identity}, in cluster: {cluster.name}, are up-to-date.')


def _delete(cluster: Cluster, delete_user_group_json):
    logger = logging.getLogger(__name__)
    user_group_identity = delete_user_group_json['component']['identity']

    delete_url = '/' + url_helper.construct_path_parts(['tenants', 'user-groups', delete_user_group_json['id']])
    try:
        response = requests.delete(
            **cluster._get_connection_details(delete_url),
            params={'version': str(delete_user_group_json['revision']['version'])})
        if response.status_code != 200:
            logger.warning(f'Unable to delete user group: {user_group_identity}, from cluster: {cluster.name}.')
            logger.warning(response.text)
            return
        logger.info(f'Deleted user group: {user_group_identity}, from cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to delete user group: {user_group_identity}, from cluster: {cluster.name}.')
        logger.warning(exception)


def _did_members_change(user_group: UserGroup, current_user_group_json):
    if len(user_group.members) != len(current_user_group_json['component']['users']):
        return True

    for user_identity in user_group.members:
        users = [
            u for u in current_user_group_json['component']['users']
            if u['component']['identity'].lower() == user_identity.lower()
        ]

        if len(users) == 0:
            return True

    return False
