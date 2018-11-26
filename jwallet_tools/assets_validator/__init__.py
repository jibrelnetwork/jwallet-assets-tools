from jsonschema import Draft4Validator
from jsonschema.validators import extend

from .contract import ContractValidator
from .utils import load_json


def create_assets_validator(*args, **kwargs):
    """ Create validator for assets.

    Add ContractValidator to default jsonschema validator and pass all received
    arguments to ContractValidator constructor.

    :param args: see ContractValidator args
    :param kwargs: see ContractValidator kwargs
    :return: jsonschema.Draft4Validator
    """
    assets_validator = extend(Draft4Validator, validators={
        'isValidContract': ContractValidator(
            *args, **kwargs
        )
    })

    return assets_validator(load_json('assets.schema.json'))
