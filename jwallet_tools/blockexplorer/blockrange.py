import logging


logger = logging.getLogger(__name__)

MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE = 10 ** 5

EXCEPTION_SPEED_FACTOR = 0.1
SPEED_CHANGE_FACTOR = 1
MAX_CHANGE_RATIO = 10

TARGET_TIME = 2


class VariableBlockRange:

    """Variable block range.

    Like `range` but step can be managed in runtime.
    """

    def __init__(self, from_block, to_block, reverse=False, batch_size=1000):
        self.from_block = from_block
        self.to_block = to_block

        self.reverse = reverse
        if reverse:
            self.from_block, self.to_block = self.to_block, self.from_block

        self.direction = -1 if reverse else 1
        self.batch_size = batch_size
        self.new_batch_size = None
        self.reset_next = False

    def set_step(self, batch_size):
        """Set batch size on next iteration.

        :param batch_size:
        :param reset:
        :return:
        """
        if batch_size == self.batch_size:
            return
        self.new_batch_size = batch_size

    def rollback(self):
        self.reset_next = True

    def __iter__(self):
        from_block = self.from_block
        step = self.batch_size * self.direction

        while True:
            if self.new_batch_size:
                self.new_batch_size, self.batch_size = None, self.new_batch_size
                step = self.batch_size * self.direction

            for from_block in range(self.from_block, self.to_block + 1, step):
                to_block = from_block + step - self.direction
                if self.to_block_overflow(to_block):
                    to_block = self.to_block

                if self.reverse:
                    yield to_block, from_block
                else:
                    yield from_block, to_block

                if self.reset_next:
                    logger.debug('rollback last interval')
                    self.reset_next = False
                    break

                self.from_block = from_block + step

                if self.new_batch_size:
                    logger.debug('break to change new batch size')
                    break
            else:
                break

        if not self.reverse and self.from_block < self.to_block:
            # tail
            yield from_block, self.to_block
        elif self.reverse and self.to_block != to_block:
            yield self.to_block + 1, to_block

    def to_block_overflow(self, to_block):
        return (
            not self.reverse and to_block > self.to_block
        ) or (
            self.reverse and to_block < self.to_block
        )


class ThrottledBlockRange(VariableBlockRange):
    def update(self, last_measurement):
        ratio = (TARGET_TIME / last_measurement) * SPEED_CHANGE_FACTOR
        if abs(ratio) > MAX_CHANGE_RATIO:
            ratio = MAX_CHANGE_RATIO * self.direction

        new_batch_size = int(self.batch_size * ratio)

        if new_batch_size > MAX_BATCH_SIZE:
            new_batch_size = MAX_BATCH_SIZE

        if new_batch_size > self.batch_size:
            logger.debug("[up] batch size to %i (from %i)", new_batch_size, self.batch_size)
        elif new_batch_size < self.batch_size:
            logger.debug("[down] batch size to %i (from %i)", new_batch_size, self.batch_size)
        self.set_step(new_batch_size)
