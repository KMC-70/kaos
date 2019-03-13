"""Contains the schemas used to verify JSON requests/responses as well as their validators."""

from jsonschema.validators import Draft7Validator

SEARCH_SCHEMA = {
    '$schema': 'https://json-schema.org/schema#',
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'Target': {
            'type': 'array',
            'items': {'type': "number"},
            'minItems': 2,
            'maxItems': 2,
        },
        'POI': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'startTime': {'type': 'string'},
                'endTime': {'type': 'string'},
            },
            'required': ['startTime', 'endTime'],
        },
        'PlatformID': {
            'type': 'array',
            'items': {'type': "number"},
            'minItems': 1,
        },
    },
    'required': ['Target', 'POI'],
}


OPERTUNITY_SCHEMA = {
    '$schema': 'https://json-schema.org/schema#',
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'TargetArea': {
            'type': 'array',
            'items': {
                'type': 'array',
                'minItems': 2,
                'maxItems': 2,
            },
            'minItems': 3,
        },
        'POI': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'startTime': {'type': 'string'},
                'endTime': {'type': 'string'},
            },
            'required': ['startTime', 'endTime'],
        },
        'PlatformID': {
            'type': 'array',
            'items': {'type': "number"},
            'minItems': 1,
        },
    },
    'required': ['TargetArea', 'POI'],
}

SEARCH_QUERY_VALIDATOR = Draft7Validator(SEARCH_SCHEMA)
OPERTUNITY_QUERY_VALIDATOR = Draft7Validator(OPERTUNITY_SCHEMA)
