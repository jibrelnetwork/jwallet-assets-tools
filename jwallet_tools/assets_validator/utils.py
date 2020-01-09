import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from tdigest import TDigest
from jsonschema import ValidationError
from web3 import Web3


TOOLS_ROOT = Path(os.path.dirname(__file__)) / '..'


logger = logging.getLogger(__name__)


def load_json(filename):
    return json.load(open(TOOLS_ROOT / filename, 'r'))


def make_signature(method_name, inputs):
    """Make method signature from its name and inputs.

    :param method_name: method name
    :param inputs: method inputs (from abi)
    :return: method signature usable for hashing and byte-code search
    """
    arg_types = ','.join([input_['type'] for input_ in inputs])
    return f"{method_name}({arg_types})"


def signature_exist(code, signature) -> bool:
    """Check if signature exist in contract byte-code.

    :param code: Contract byte-code
    :param signature: method signature
    :return: True if signature found in byte-code
    """
    fn_hash = Web3.sha3(signature.encode('utf-8'))
    return fn_hash.hex()[2:10] in code.hex()


def normalize_address(address):
    """Normalize contract address.

    Convert to ChecksumAddress if it wasn't.

    :param address: contract address (checksum or not)
    :return: normalized address
    """
    if not Web3.isChecksumAddress(address):
        address = Web3.toChecksumAddress(address)

    return address


class IgnoreLoggerAdapter(logging.LoggerAdapter):
    @property
    def token_name(self):
        token = self.extra['token']
        return '%s (%s)' % (token['name'], token['symbol'])

    def ignore(self, msg, *args, **kwargs):
        self.debug(f'[I] {self.token_name}: {msg}', *args, **kwargs)

    def if_ignored(self, method_name, message, *args):
        """Log message if ignored or yield ValidationError

        :param method_name: method name
        :param message: log message
        :param args: message args
        """
        if self._method_ignored(method_name):
            self.ignore(f"{method_name}: {message}", *args)
        else:
            yield ValidationError(f"{method_name}: {message % args}")

    def _method_ignored(self, method):
        """Check if method ignored.

        :param method: contract method name
        :return:
        """
        symbol = self.extra['token']['symbol']
        variants = [
            method,
            f'{symbol}.{method}',
            f'{symbol}.*',
            f'*.{method}',
        ]

        return any([v in self.extra['ignore'] for v in variants])


class RangedTDigest:

    """Ranged TDigest.

    Store TDigest instance per configured interval. For ex.: with intervals `[10,20]`,
    two tdigest will be stored: for x<=10, and 20 <= x < 10.
    """

    by_range: Dict[int, TDigest]

    def __init__(self, ranges: List[int], delta=0.01, k=25):
        self.ranges = ranges
        self.by_range = {x: TDigest(delta, k) for x in ranges}

    def percentile(self, range, percentile):
        return self.by_range[range].percentile(percentile)

    def update(self, range_value: int, value: float):
        for range_end in sorted(self.by_range):
            if range_end > range_value:
                self.by_range[range_end].update(value)
                break

    def max_percentile(self, percentile) -> float:
        return max(*[x[1] for x in self.all(percentile)])

    def all(self, percentile) -> List[Tuple[int, float]]:
        result: List[Tuple[int, float]] = []
        for _range, tdigest in self.by_range.items():
            value = 0
            if tdigest.n > 0:
                value = tdigest.percentile(percentile)
            else:
                logger.debug("No values for range %i", _range)
            result.append((_range, value))
        return result


def get_block_by_date(web3, target_date):
    """ Search for any block on given date """
    average_block_time = 17 * 1.5

    target_timestamp = int(target_date.timestamp())
    block = web3.eth.getBlock(web3.eth.blockNumber)
    block_number = block['number']
    delta = -1
    while delta != 0:
        delta = int((target_timestamp - block['timestamp']) / average_block_time)
        block_number += delta
        block = web3.eth.getBlock(block_number)
    return block
