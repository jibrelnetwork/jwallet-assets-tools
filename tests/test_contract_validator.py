from unittest import mock
import pytest

from web3 import Web3, HTTPProvider
from web3.datastructures import AttributeDict

from .fixtures import (
    TEST_TOKEN_ADDRESS,
    TEST_TOKEN_GAS,
    TEST_TOKEN_DEPLOYMENT_BLOCK,
    TEST_TOKEN_DECIMALS,

    w3,  # noqa
    validator,  # noqa
    contract,  # noqa
)


NODE_URL = "https://main-node.jwallet.network/"


TEST_TOKEN_ADDRESS = Web3.toChecksumAddress("0xa15c7ebe1f07caf6bff097d8a589fb8ac49ae5b3")
TEST_TOKEN_GAS = 39242
TEST_TOKEN_DEPLOYMENT_BLOCK = 5217268
TEST_TOKEN_DECIMALS = 18


def test_known_gas_amount(validator, contract):
    receipts_mock = mock.MagicMock()
    receipts_mock.return_value.return_value = [
        AttributeDict({'gasUsed': TEST_TOKEN_GAS, 'blockNumber': 5 * 10 ** 6})
    ]
    with mock.patch('jwallet_tools.assets_validator.contract.EventReceiptIterator'):
        with pytest.raises(StopIteration):
            next(iter(
                validator.validate_static_gas_amount(
                    contract, TEST_TOKEN_GAS, TEST_TOKEN_DEPLOYMENT_BLOCK
                )
            ))


def test_validate_methods(w3, validator, contract):
    code = w3.eth.getCode(TEST_TOKEN_ADDRESS)

    with pytest.raises(StopIteration):
        next(iter(
            validator.validate_methods(contract, code)
        ))


def test_validate_decimals(validator, contract):
    with pytest.raises(StopIteration):
        next(iter(
            validator.validate_decimals(contract, TEST_TOKEN_DECIMALS)
        ))


def test_main_method(validator, validator_args):
    with mock.patch.object(validator, 'validate_static_gas_amount'):
        with pytest.raises(StopIteration):
            next(iter(
                validator(*validator_args)
            ))


def test_no_address(validator, validator_args):
    validator_args[2] = {
        'blockchainParams': {
            "type": "erc-20"
        }
    }
    assert len(list(validator(*validator_args))) == 1


def test_invalid_address(validator, validator_args):
    with mock.patch.object(validator, 'validate_static_gas_amount'):
        validator_args[2] = {
            'blockchainParams': {
                "type": "erc-20",
                "address": "invalid"
            }
        }
        assert len(list(validator(*validator_args))) == 1


def test_no_decimals(validator, validator_args):
    with mock.patch.object(validator, 'validate_static_gas_amount'):
        validator_args[2] = {
            'blockchainParams': {
                "type": "erc-20",
                "address": "0xa15c7ebe1f07caf6bff097d8a589fb8ac49ae5b3",
            }
        }
        assert len(list(validator(*validator_args))) == 1


@pytest.fixture
def validator_args():
    return [
        None,
        {},
        {
            "name": "Pundi X",
            "symbol": "PXS",
            "blockchainParams": {
                "type": "erc-20",
                "address": TEST_TOKEN_ADDRESS,
                "decimals": TEST_TOKEN_DECIMALS,
                "staticGasAmount": TEST_TOKEN_GAS,
                "deploymentBlockNumber": TEST_TOKEN_DEPLOYMENT_BLOCK
            }
        },
        None
    ]
