from .certificate_config import CertificateConfig


class ClusterSecurity:

    def __init__(self, security: dict):
        self.use_certificate = security['use_certificate']

        if self.use_certificate:
            self.certificate_config = CertificateConfig(security['certificate_config'])


class User():

    def __init__(self, identity: str):
        self.identity = identity
        self.component_id = ''
        self.revision_version = 0


class UserGroup(User):

    def __init__(self, identity: str, members: list):
        self.members = members if not(members is None) else []
        User.__init__(self, identity)


class GlobalAccessPolicy:

    def __init__(self, name: str, action: str, users: list, user_groups: list):
        self.name = name
        self.action = action
        self.users = users if not(users is None) else []
        self.user_groups = user_groups if not(user_groups is None) else []


class ComponentAccessPolicy:

    def __init__(
        self, name: str,
        component_type: str,
        component_name: str,
        users: list,
        user_groups: list,
        inherited: bool,
        clusters: list
    ):
        self.name = name
        self.component_type = component_type
        self.component_name = component_name
        self.users = users if not(users is None) else []
        self.user_groups = user_groups if not(user_groups is None) else []
        self.inherited = inherited
        self.clusters = clusters if not(clusters is None) else []


class Security:

    def __init__(self, security: dict):
        self.is_coordinated = security['is_coordinated']
        self.users = [
            User(identity=user_identity) for user_identity in security['users']
        ] if 'users' in security and not(security['users'] is None) else []

        self.user_groups = [
            UserGroup(
                identity=ug['identity'],
                members=ug['members'] if 'members' in ug else [])
            for ug in security['user_groups']
        ] if 'user_groups' in security and not(security['user_groups'] is None) else []

        self.global_access_policies = [
            GlobalAccessPolicy(
                name=gap['name'],
                action=gap['action'],
                users=gap['users'] if 'users' in gap else [],
                user_groups=gap['user_groups'] if 'user_groups' in gap else [])
            for gap in security['global_access_policies']
        ] if 'global_access_policies' in security and not(security['global_access_policies'] is None) else []

        self.component_access_policies = [
            ComponentAccessPolicy(
                name=cap['name'],
                component_type=cap['component_type'],
                component_name=cap['component_name'],
                users=cap['users'] if 'users' in cap else [],
                user_groups=cap['user_groups'] if 'user_groups' in cap else [],
                inherited=cap['inherited'] if 'inherited' in cap else False,
                clusters=cap['clusters'] if 'clusters' in cap else [])
            for cap in security['component_access_policies']
        ] if 'component_access_policies' in security and not(security['component_access_policies'] is None) else []


class AccessPolicyDescriptor:

    def __init__(self, name: str, resource: str, action: str, required_by_coordinator: bool):
        self.name = name
        self.resource = resource
        self.action = action
        self.required_by_coordinator = required_by_coordinator
