import logging

from jwallet_tools.blockexplorer.events import EventReceiptIterator

from .conftest import (
    TEST_TOKEN_ADDRESS,
)


BLOCKS_WITH_TEST_TX = 6778138


def test_iterate_receipts(w3, caplog):
    caplog.set_level(logging.DEBUG)
    iterator = EventReceiptIterator(
        w3, TEST_TOKEN_ADDRESS,
        # there are some events, according to etherscan :-)
        BLOCKS_WITH_TEST_TX, BLOCKS_WITH_TEST_TX,
        concurrency=1, progress=True
    )
    next(iter(iterator))
