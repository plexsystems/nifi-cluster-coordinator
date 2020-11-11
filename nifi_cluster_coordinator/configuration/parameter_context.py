class Parameter:

    def __init__(self, name, description, is_sensitive, value):
        self.name = name
        self.description = description
        self.is_sensitive = is_sensitive
        self.value = value


class ParameterContext:

    def __init__(self, name, description, is_coordinated, parameters):
        self.name = name
        self.description = description
        self.is_coordinated = is_coordinated
        self.parameters = [
            Parameter(
                name=p['name'],
                description=p['description'],
                is_sensitive=p['is_sensitive'],
                value=p['value'])
            for p in parameters
        ] if not (parameters is None) else []
        self.id = None
