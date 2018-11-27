import logging

from jwallet_tools.blockexplorer.events import EventReceiptIterator
from jwallet_tools.assets_validator.contract import TRANSFER_ABI, construct_event_topic_set

from .fixtures import (
    TEST_TOKEN_ADDRESS,
    TEST_TOKEN_DEPLOYMENT_BLOCK,
    w3,  # noqa
)


def test_iterate_receipts(w3, caplog):
    caplog.set_level(logging.DEBUG)
    iterator = EventReceiptIterator(
        w3, TEST_TOKEN_ADDRESS,
        6778138, 6778138,  # there are some events, according to etherscan :-)
        concurrency=1, progress=True
    )
    next(iter(iterator))
