import pytest

from web3 import Web3, HTTPProvider
from jwallet_tools.assets_validator.contract import ERC20_ABI, ContractValidator


NODE_URL = "https://main-node.jwallet.network/"

TEST_TOKEN_ADDRESS = Web3.toChecksumAddress("0xa15c7ebe1f07caf6bff097d8a589fb8ac49ae5b3")
TEST_TOKEN_GAS = 39242
TEST_TOKEN_DEPLOYMENT_BLOCK = 5217268
TEST_TOKEN_DECIMALS = 18


@pytest.fixture()
def w3():
    node_url = "https://main-node.jwallet.network/"
    return Web3(HTTPProvider(node_url))


@pytest.fixture
def validator():
    return ContractValidator(NODE_URL)


@pytest.fixture
def contract(w3):
    return w3.eth.contract(TEST_TOKEN_ADDRESS, abi=ERC20_ABI)
