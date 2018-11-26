import os
import json
import logging
from pathlib import Path

from jsonschema import ValidationError
from web3 import Web3


TOOLS_ROOT = Path(os.path.dirname(__file__)) / '..'


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
