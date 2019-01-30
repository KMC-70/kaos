"""Validators for DB models."""

import flask_validator


class ValidateString(flask_validator.ValidateString):
    """Modified string validator that supports non empty string enforcement."""
    def __init__(self, field, allow_empty=False, **kwargs):
        flask_validator.ValidateString.__init__(self, field, **kwargs)
        self.allow_empty = allow_empty

    def check_value(self, value):
        """Check that the value supplied to the model is a string and does match the specified
        validator parameters.
        """
        if flask_validator.ValidateString.check_value(self, value) and (self.allow_empty or value):
            return True

        return None
