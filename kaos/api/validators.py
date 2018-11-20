"""This module defines the validation decorators used by the various view functions."""

from functools import wraps

from flask import request

from .errors import APIError, InputSchemaError


def validate_request_schema(schema_validator):
    """Validation decorator used to ensure that incomming requests to the view follow a specific
    json schema.

    Args:
        schema_validator (fn): A scgema validation object used to check the request for errors.

    Returns: A validation function decorator that wraps view functions in schema_validator.
    """
    def validation_fucntion(view_fn):
        """Wraps a view function and ensures that the request matches the schema_validator.

        Args:
            view_fn (fn): The view function to protect.

        Returns: The protected view function.
        """

        @wraps(view_fn)
        def validated_function(*args, **kwargs):
            """Wrapper function that checks that a request conforms to a schema_validator before
            calling the underlying view function.

            Args:
                *args: Perfect positional argument forwarding.
                *kwargs: Perfect keyword argument forwarding.
            """

            if not request.json:
                raise APIError({'MimeType': 'Expected application/json'})

            errors = list(schema_validator.iter_errors(request.json))
            if errors:
                raise InputSchemaError(errors)

            return view_fn(*args, **kwargs)

        return validated_function

    return validation_fucntion
