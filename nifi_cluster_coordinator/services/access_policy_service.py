import logging
import requests
import utils.url_helper as url_helper
from configuration.cluster import Cluster
from configuration.security import AccessPolicyDescriptor, ComponentAccessPolicy, Security


def init_access_policies_descriptors():
    global global_access_policies_descriptors, component_access_policies_descriptors

    global_access_policies_descriptors = [
        AccessPolicyDescriptor('view the UI', 'flow', 'read'),
        AccessPolicyDescriptor('access the controller', 'controller', 'read'),
        AccessPolicyDescriptor('access the controller', 'controller', 'write'),
        AccessPolicyDescriptor('access parameter contexts', 'parameter-contexts', 'read'),
        AccessPolicyDescriptor('access parameter contexts', 'parameter-contexts', 'write'),
        AccessPolicyDescriptor('query provenance', 'provenance', 'read'),
        AccessPolicyDescriptor('access restricted components', 'restricted-components', 'read'),
        AccessPolicyDescriptor('access restricted components', 'restricted-components', 'write'),
        AccessPolicyDescriptor('access all policies', 'policies', 'read'),
        AccessPolicyDescriptor('access all policies', 'policies', 'write'),
        AccessPolicyDescriptor('access users/user groups', 'tenants', 'read'),
        AccessPolicyDescriptor('access users/user groups', 'tenants', 'write'),
        AccessPolicyDescriptor('retrieve site-to-site details', 'site-to-site', 'read'),
        AccessPolicyDescriptor('view system diagnostics', 'system', 'read'),
        AccessPolicyDescriptor('proxy user requests', 'proxy', 'read'),
        AccessPolicyDescriptor('access counters', 'counters', 'read'),
        AccessPolicyDescriptor('access counters', 'counters', 'write')
    ]

    component_access_policies_descriptors = [
        AccessPolicyDescriptor('view the component', 'process-groups/{id}', 'read'),
        AccessPolicyDescriptor('modify the component', 'process-groups/{id}', 'write'),
        AccessPolicyDescriptor('operate the component', 'operation/process-groups/{id}', 'write'),
        AccessPolicyDescriptor('view provenance', 'provenance-data/process-groups/{id}', 'read'),
        AccessPolicyDescriptor('view the data', 'data/process-groups/{id}', 'read'),
        AccessPolicyDescriptor('modify the data', 'data/process-groups/{id}', 'write'),
        AccessPolicyDescriptor('view the policies', 'policies/process-groups/{id}', 'read'),
        AccessPolicyDescriptor('modify the policies', 'policies/process-groups/{id}', 'write')
    ]


def sync(cluster: Cluster, security: Security, configured_projects: list):
    """Set the cluster users to desired configuration."""
    logger = logging.getLogger(__name__)

    logger.info(f'Getting coordinator user for cluster: {cluster.name}')
    current_user_json = _get_current_user_json(cluster)

    # sync global policies
    for access_policy_descriptor in global_access_policies_descriptors:
        configured_access_policies = [
            a for a in security.global_access_policies
            if a.name.lower() == access_policy_descriptor.name.lower()
            and a.action.lower() == access_policy_descriptor.action.lower()
        ]

        access_policy_json = _get_access_policy_json(cluster, access_policy_descriptor, None)
        if len(configured_access_policies) == 0:
            if not(access_policy_json is None):
                if _does_current_user_has_policy(access_policy_descriptor.action, access_policy_descriptor.resource, current_user_json):
                    _update(
                        cluster,
                        access_policy_descriptor,
                        [],
                        [],
                        security.users,
                        security.user_groups,
                        access_policy_json,
                        current_user_json,
                        None)
                else:
                    _delete(cluster, access_policy_descriptor, access_policy_json)
        else:
            configured_access_policy = configured_access_policies[0]
            if access_policy_json is None:
                _create(
                    cluster,
                    access_policy_descriptor,
                    configured_access_policy.users,
                    configured_access_policy.user_groups,
                    security.users,
                    security.user_groups,
                    None)
            else:
                _update(
                    cluster,
                    access_policy_descriptor,
                    configured_access_policy.users,
                    configured_access_policy.user_groups,
                    security.users,
                    security.user_groups,
                    access_policy_json,
                    current_user_json,
                    None)

    # sync component policies
    for access_policy_descriptor in component_access_policies_descriptors:
        configured_access_policies = [
            a for a in security.component_access_policies
            if a.name.lower() == access_policy_descriptor.name.lower()
        ]

        for configured_access_policy in configured_access_policies:
            component_id = _get_component_id(cluster, configured_access_policy, configured_projects)
            if not component_id:
                logger.warning(
                    f'Unable to find component: {configured_access_policy.component_type}/{configured_access_policy.component_name}, in cluster: {cluster.name}.')
            else:
                access_policy_json = _get_access_policy_json(cluster, access_policy_descriptor, component_id)
                if access_policy_json is None:
                    _create(
                        cluster,
                        access_policy_descriptor,
                        configured_access_policy.users,
                        configured_access_policy.user_groups,
                        security.users,
                        security.user_groups,
                        component_id)
                else:
                    _update(
                        cluster,
                        access_policy_descriptor,
                        configured_access_policy.users,
                        configured_access_policy.user_groups,
                        security.users,
                        security.user_groups,
                        access_policy_json,
                        current_user_json,
                        component_id)


def _create(
    cluster: Cluster,
    access_policy_descriptor: AccessPolicyDescriptor,
    policy_users: list,
    policy_user_groups: list,
    configured_users: list,
    configured_user_groups: list,
    component_id: str
):
    logger = logging.getLogger(__name__)

    resource = access_policy_descriptor.resource
    if component_id:
        resource = resource.replace('{id}', component_id)

    create_json = {
        'revision': {
            'version': 0
        },
        'component': {
            'resource': '/' + resource,
            'action': access_policy_descriptor.action,
            'users': _get_access_policy_users_json(policy_users, configured_users),
            'userGroups': _get_access_policy_user_groups_json(policy_user_groups, configured_user_groups)
        }
    }

    try:
        response = requests.post(
            **cluster._get_connection_details(
                '/' + url_helper.construct_path_parts(['policies'])), json=create_json)
        if response.status_code != 201:
            logger.warning(
                f'Unable to create access policy: {access_policy_descriptor.action}/{resource}, in cluster: {cluster.name}.')
            logger.warning(response.text)
            return
        logger.info(
            f'Created access policy: {access_policy_descriptor.action}/{resource}, in cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(
            f'Unable to create access policy: {access_policy_descriptor.action}/{resource}, cluster: {cluster.name}.')
        logger.warning(exception)


def _update(
    cluster: Cluster,
    access_policy_descriptor: AccessPolicyDescriptor,
    policy_users: list,
    policy_user_groups: list,
    configured_users: list,
    configured_user_groups: list,
    current_access_policy_json,
    current_user_json,
    component_id: str
):
    logger = logging.getLogger(__name__)

    resource = access_policy_descriptor.resource
    if component_id:
        resource = resource.replace('{id}', component_id)

    desired_policy_users = [p for p in policy_users]
    append_current_user = _does_current_user_has_policy(access_policy_descriptor.action, resource, current_user_json)
    if append_current_user:
        desired_policy_users.append(current_user_json['component']['identity'])

    if _did_users_or_groups_change(desired_policy_users, policy_user_groups, current_access_policy_json):

        url = '/' + url_helper.construct_path_parts(['policies', current_access_policy_json['id']])
        current_access_policy_json['component']['users'] = _get_access_policy_users_json(policy_users, configured_users)
        current_access_policy_json['component']['userGroups'] = _get_access_policy_user_groups_json(policy_user_groups, configured_user_groups)

        if append_current_user:
            current_access_policy_json['component']['users'].append({
                'revision': current_user_json['revision'],
                'id': current_user_json['id'],
                'component': {
                    'id': current_user_json['id'],
                    'identity': current_user_json['component']['identity']
                }
            })

        try:
            response = requests.put(**cluster._get_connection_details(url), json=current_access_policy_json)
            if response.status_code != 200:
                logger.warning(f'Unable to update access policy: {access_policy_descriptor.action}/{resource}, in cluster: {cluster.name}.')
                logger.warning(response.text)
                return
            logger.info(f'Updated access policy: {access_policy_descriptor.action}/{resource}, in cluster: {cluster.name}.')
        except requests.exceptions.RequestException as exception:
            logger.warning(f'Unable to update access policy: {access_policy_descriptor.action}/{resource}, in cluster: {cluster.name}.')
            logger.warning(exception)
    else:
        logger.info(f'Access policicy: {access_policy_descriptor.action}/{resource}, in cluster: {cluster.name}, is up-to-date.')


def _delete(cluster: Cluster, access_policy_descriptor: AccessPolicyDescriptor, delete_access_policy_json):
    logger = logging.getLogger(__name__)

    delete_url = '/' + url_helper.construct_path_parts(['policies', delete_access_policy_json['id']])
    try:
        response = requests.delete(
            **cluster._get_connection_details(delete_url),
            params={'version': str(delete_access_policy_json['revision']['version'])})
        if response.status_code != 200:
            logger.warning(
                f'Unable to delete access policy: {access_policy_descriptor.action}/{access_policy_descriptor.resource}, from cluster: {cluster.name}.')
            logger.warning(response.text)
            return
        logger.info(
            f'Deleted access policy: {access_policy_descriptor.action}/{access_policy_descriptor.resource}, from cluster: {cluster.name}.')
    except requests.exceptions.RequestException as exception:
        logger.warning(
            f'Unable to delete access policy: {access_policy_descriptor.action}/{access_policy_descriptor.resource}, from cluster: {cluster.name}.')
        logger.warning(exception)


def _get_access_policy_json(cluster: Cluster, access_policy_descriptor: AccessPolicyDescriptor, component_id: str):
    logger = logging.getLogger(__name__)

    resource = access_policy_descriptor.resource
    if component_id:
        resource = resource.replace('{id}', component_id)

    try:
        response = requests.get(
            **cluster._get_connection_details(
                '/' + url_helper.construct_path_parts(['policies', access_policy_descriptor.action, resource])))
        if response.status_code != 200:
            return None
        return response.json()
    except requests.exceptions.RequestException as exception:
        logger.warning(
            f'Unable to get access policy by action: {access_policy_descriptor.action}, resource: {resource}, in cluster: {cluster.name}.')
        logger.warning(exception)

    return None


def _get_current_user_json(cluster: Cluster):
    current_user_identity = requests.get(
        **cluster._get_connection_details(
            '/' + url_helper.construct_path_parts(['flow', 'current-user']))).json()['identity']

    users_json = requests.get(
        **cluster._get_connection_details(
            '/' + url_helper.construct_path_parts(['tenants', 'users']))).json()

    current_user_jsons = [
        u for u in users_json['users']
        if u['component']['identity'].lower() == current_user_identity.lower()
    ]

    if len(current_user_jsons) > 0:
        return current_user_jsons[0]

    return None


def _get_component_id(cluster: Cluster, component_access_policy: ComponentAccessPolicy, configured_projects: list):
    if (
        component_access_policy.component_type.lower() == 'nifi flow'
        and component_access_policy.component_name.lower() == 'root'
    ):
        return cluster.root_process_group_id

    for project in list(
        filter(
            lambda p: len([c for c in p.clusters if c.name.lower() == cluster.name.lower()]) > 0, configured_projects)):

        project_cluster = project.get_project_cluster(cluster)

        if not(project_cluster is None):
            if component_access_policy.component_type.lower() == 'project':
                if component_access_policy.component_name.lower() == project.name.lower():
                    return project_cluster.project_process_group_id

            elif component_access_policy.component_type.lower() == 'environment':
                component_name_parts = component_access_policy.component_name.split(':')

                if component_name_parts[0].lower() == project.name.lower():
                    environments = [e for e in project_cluster.environments if e.name.lower() == component_name_parts[1].lower()]
                    if len(environments) > 0:
                        return environments[0].process_group_id

    return None


def _did_users_or_groups_change(policy_users: list, policy_user_groups: list, current_acccess_policy_json):
    if len(policy_users) != len(current_acccess_policy_json['component']['users']):
        return True

    if len(policy_user_groups) != len(current_acccess_policy_json['component']['userGroups']):
        return True

    for user_identity in policy_users:
        users = [
            u for u in current_acccess_policy_json['component']['users']
            if u['component']['identity'].lower() == user_identity.lower()
        ]

        if len(users) == 0:
            return True

    for user_group_identity in policy_user_groups:
        user_groups = [
            ug for ug in current_acccess_policy_json['component']['userGroups']
            if ug['component']['identity'].lower() == user_group_identity.lower()
        ]

        if len(user_groups) == 0:
            return True

    return False


def _get_access_policy_users_json(policy_users: list, configured_users: list):
    logger = logging.getLogger(__name__)

    users_json = []
    for user_identity in policy_users:
        users = [u for u in configured_users if u.identity.lower() == user_identity.lower()]
        if len(users) > 0:
            users_json.append({
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
            logger.warning(f'User: {user_identity}, not found in configured users.')

    return users_json


def _get_access_policy_user_groups_json(policy_user_groups: list, configured_user_groups: list):
    logger = logging.getLogger(__name__)

    users_groups_json = []
    for user_group_identity in policy_user_groups:
        user_groups = [ug for ug in configured_user_groups if ug.identity.lower() == user_group_identity.lower()]
        if len(user_groups) > 0:
            users_groups_json.append({
                'revision': {
                    'version': 0
                },
                'id': user_groups[0].component_id,
                'component': {
                    'identity': user_group_identity,
                    'id': user_groups[0].component_id
                }
            })
        else:
            logger.warning(f'User group: {user_group_identity}, not found in configured user groups.')

    return users_groups_json


def _does_current_user_has_policy(action: str, resource: str, current_user_json):
    access_policies = [
        p for p in current_user_json['component']['accessPolicies']
        if p['component']['action'].lower() == action.lower()
        and p['component']['resource'].lower() == '/' + resource.lower()
    ]

    if len(access_policies) > 0:
        return True

    return False
