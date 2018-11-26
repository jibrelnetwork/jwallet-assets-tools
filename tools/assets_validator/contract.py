import logging

from tdigest import TDigest
from jsonschema import ValidationError

from web3 import Web3
from web3.exceptions import BadFunctionCallOutput
from web3.utils.events import construct_event_topic_set

from ..blockexplorer.events import EventReceiptIterator

from .utils import (
    IgnoreLoggerAdapter,
    normalize_address,
    make_signature,
    signature_exist,
    load_json
)
from ._http_provider import CustomHTTPProvider


logger = logging.getLogger(__name__)

NODE_REQUEST_TIMEOUT = 3

LAST_HARD_FORK_BLOCK = 4370000

ERC20_ABI = load_json('erc20_abi.json')

TRANSFER_ABI = list(filter(lambda x: x.get('name') == 'Transfer', ERC20_ABI))[0]


class ContractValidator:

    """
    ERC20 contract validator for jsonschema.

    Check if:

    - contract exist and not empty
    - contract has ERC20 methods and signature matched
    - decimals stored in json equals to actual contract decimals

    Also calculate and check `staticGasAmount` if `fast is True`.
    """

    gas_amount_percentile = 100

    def __init__(self, node, ignore=None, fast=False, progress=False):
        """Constructor.

        :param node: ethereum node to use
        :param ignore: list of ignored contract methods
        :param fast: do not invoke methods to test
        :param quiet: do not output ignore logs (if True)
        """
        self.node = node
        self.ignore = set() if ignore is None else set(ignore)
        self.fast = fast
        self.progress = progress

        self.log = IgnoreLoggerAdapter(logger, extra={})

        self.web3 = Web3(CustomHTTPProvider(self.node, request_kwargs={
            'timeout': NODE_REQUEST_TIMEOUT
        }))

    def __call__(self, validator, value, instance, schema):
        """Validate whole contract consistency.

        :param value: validator config from schema
        :param instance: contract dict from json
        """
        blockchain_params = instance.get('blockchainParams', {})
        if blockchain_params.get('type') != 'erc-20':
            return

        self.log.extra = {
            'token': instance,
            'ignore': self.ignore.union(value.get('ignore', set()))
        }

        self.log.info("%s validation", instance.get('symbol'))

        address = blockchain_params.get('address')

        if not address:
            yield ValidationError('`address` is required')
            return

        if not self.web3.isAddress(address):
            yield ValidationError("%s is not an address" % address)
            return

        address = normalize_address(address)

        if not self.fast:
            contract = self.web3.eth.contract(address, abi=ERC20_ABI)
            code = self.web3.eth.getCode(address)
            if not code:
                yield from self.log.if_ignored("code", "Contract code is empty")
                return

            yield from self.validate_methods(contract, code)

            yield from self.validate_decimals(contract, blockchain_params.get('decimals'))

            deployment_block = blockchain_params.get('deploymentBlockNumber', 0)

            logger.debug("Validate static gas amount from %i block", deployment_block)
            yield from self.validate_static_gas_amount(
                contract,
                blockchain_params.get('staticGasAmount'),
                # TODO: must be fixed somehow in validate_deployment_block
                from_block=deployment_block
            )

    def validate_methods(self, contract, code):
        """Validate contract ERC20 methods.

        Check signature existence in byte-code and invoke safe methods
        if `fast=False`.

        :param contract: Contract instance
        :param code: contract byte-code
        :return:
        """
        for method in ERC20_ABI:
            method_name = method.get('name')

            # skip if not a function
            if method.get('type') != 'function':
                continue

            yield from self.validate_signature(code, method_name, method['inputs'])

            # call method if no arguments required and `fast` is not True
            # also do not invoke decimals because it invoked in validate_deciamals
            if self.fast or method.get('inputs') != [] or method_name == 'decimals':
                continue

            try:
                getattr(contract.functions, method_name)().call()
            except Exception as e:
                yield from self.log.if_ignored(method_name, str(e))

    def validate_decimals(self, contract, expected):
        """Check that decimals defined in json equals to actual value.

        :param contract: Contract instance
        :param expected: expected decimals value
        """
        try:
            actual = contract.functions.decimals().call()

            if actual != expected:
                yield ValidationError(
                    "Value doesn't match `decimals` value from contract, "
                    "expected %s (actual: %s)" % (
                        expected,
                        actual
                    )
                )
        except BadFunctionCallOutput as e:
            yield from self.log.if_ignored('decimals', str(e))

    def validate_static_gas_amount(self, contract, expected_max_gas, from_block):
        """Validate gas amount.

        Iterate over contract TXs using EventReceiptIterator.

        :param contract: Contract instance to validate
        :param expected_max_gas: expected static gas amount (from source json)
        """
        to_block = self.web3.eth.blockNumber
        last_fork_tdigest = TDigest()
        before_last_fork_digest = TDigest()

        topics = construct_event_topic_set(TRANSFER_ABI, dict(to=contract.address))

        for tx in EventReceiptIterator(self.web3, contract.address, from_block, to_block, topics,
                                       progress=self.progress, progress_title='staticGasAmount'):
            if tx.blockNumber >= LAST_HARD_FORK_BLOCK:
                last_fork_tdigest.update(tx.gasUsed)
            else:
                before_last_fork_digest.update(tx.gasUsed)

        max_from_fork = 0
        if last_fork_tdigest.n > 0:
            max_from_fork = last_fork_tdigest.percentile(self.gas_amount_percentile)
        else:
            self.log.debug('No transactions since last hardfork at %i block', LAST_HARD_FORK_BLOCK)

        max_before_fork = 0
        if before_last_fork_digest.n > 0:
            max_before_fork = before_last_fork_digest.percentile(self.gas_amount_percentile)
        else:
            self.log.debug('No transactions before last hardfork at %i block', LAST_HARD_FORK_BLOCK)

        max_gas_actual = max(max_from_fork, max_before_fork)

        self.log.info("staticGasAmount stats: %i overall, %i before and %i after last fork",
                      max_gas_actual, max_before_fork, max_from_fork)

        if max_gas_actual > expected_max_gas:
            yield from self.log.if_ignored(
                "staticGasAmount",
                "Expected %i gas but %i actual (P%i)" % (
                    expected_max_gas, max_gas_actual,
                    self.gas_amount_percentile
                )
            )

    def validate_signature(self, code, method_name, inputs):
        """Validate contract ERC20 method signature.

        :param code: contract byte-code
        :param method_name: method name from abi
        :param inputs: input list from abi
        """
        signature = make_signature(method_name, inputs)
        if not signature_exist(code, signature):
            msg = "signature %s not found" % signature
            yield from self.log.if_ignored(method_name, msg)
