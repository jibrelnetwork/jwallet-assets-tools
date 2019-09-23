import logging
import requests
import time
import tqdm
import urllib3

from typing import NamedTuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from web3.datastructures import AttributeDict

from .blockrange import ThrottledBlockRange

MIN_BATCH_SIZE = 2
MAX_BATCH_SIZE = 10 ** 6

EXCEPTION_SPEED_FACTOR = 0.1
SPEED_CHANGE_FACTOR = 1
MAX_CHANGE_RATIO = 2

TARGET_TIME = 2

RETRY_EXCEPTIONS = (
    requests.exceptions.RequestException,
    urllib3.exceptions.MaxRetryError
)


logger = logging.getLogger(__name__)


EventReceiptDetails = NamedTuple(
    'EventReceiptDetails',
    receipt=AttributeDict,
    transaction=AttributeDict,
)


class EventIterator:

    """Contract events iterator.

    Allow to read blocks by small chunks. Chunk size chosen regarding to
    ethereum node performance (targeting node response time to TARGET_TIME).
    """

    def __init__(self, web3, address, from_block, to_block, topics=None, batch_size=1000,
                 progress=False, progress_title=None, reverse=False):
        self.web3 = web3
        self.address = address
        self.from_block = from_block
        self.to_block = to_block
        self.topics = topics
        self.progress = progress
        self.progress_title = progress_title
        self.reverse = reverse

        self.batch_size = batch_size

        self.running = True

    def __iter__(self):
        """Iterate over contract events.

        Choose speed regarding to ethereum node performance.

        :return:
        """
        progress_bar = tqdm.tqdm(
            total=self.to_block - self.from_block,
            disable=not self.progress,
            desc=self.progress_title,
            unit='blocks',
            unit_scale=True
        )

        throttler = ThrottledBlockRange(self.from_block, self.to_block, reverse=self.reverse)

        for from_block, to_block in throttler:
            if not self.running:
                break
            try:
                logger.debug(f"Scan blocks {from_block} - {to_block} "
                             f"({to_block - from_block + 1} batch size)")

                start_time = time.time()
                log_filter = {
                    'address': self.address,
                    'fromBlock': from_block,
                    'toBlock': to_block,
                }
                if self.topics:
                    log_filter['topics'] = self.topics
                logs = self.web3.eth.getLogs(log_filter)

                result_time = time.time() - start_time
                for event in logs:
                    yield event

                progress_bar.update(throttler.batch_size)

                logger.debug('Node response time: %fs', result_time)

                throttler.update(result_time)
            except ValueError:
                # handle ValueError: {'code': -32000, 'message': 'leveldb: not found'}
                logger.exception("Problems with the node (possibly leveldb not found), "
                                 "retry after 10s")
                throttler.set_step(MIN_BATCH_SIZE)
                throttler.rollback()
                time.sleep(10)
            except RETRY_EXCEPTIONS as e:
                batch_size = int(throttler.batch_size * EXCEPTION_SPEED_FACTOR)
                if batch_size < MIN_BATCH_SIZE:
                    batch_size = MIN_BATCH_SIZE
                throttler.set_step(batch_size)
                throttler.rollback()
                logger.error("Slow down because of error to %i: %s", throttler.batch_size, e)

        progress_bar.close()


class EventReceiptIterator(EventIterator):

    """Event receipt iterator.

    Instead of parent `EventIterator` will return TX receipt instead TX itself.
    TXs will be queried on thread pool to achieve better performance (it would
    be better to switch to asyncio in future).

    Order is not guaranteed.
    """

    def __init__(self, *args, concurrency=100, **kwargs):
        """
        see EventIterator.__init__ for other options.

        :param concurrency: number of workers to start
        :param args: EventIterator args
        :param kwargs: EventIterator kwargs
        """
        super().__init__(*args, **kwargs)
        self.concurrency = concurrency

    def __iter__(self):
        """Iterate over transaction receipts gathered from parent iterator.

        Start workers, one reader thread and yield all receipts received from
        responses queue.
        """
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            pool = {executor.submit(self.get_details, item) for item in super().__iter__()}
            for future in as_completed(pool):
                yield future.result()

    def get_details(self, item):
        hash = item.get('transactionHash')
        receipt = self.web3.eth.getTransactionReceipt(hash)
        transaction = self.web3.eth.getTransaction(hash)
        details = EventReceiptDetails(receipt=receipt, transaction=transaction)
        return details
