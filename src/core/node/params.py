from enum import IntEnum


class Round(IntEnum):
    PUBLIC = 0
    COMMIT = 1
    SECRETSHARE = 2
    REVEAL = 3
    PRIVATE = 4
    FINAL = 5
    INVALID = 6


# in blocks
class Duration:
    PUBLIC = 3
    COMMIT = 3
    SECRETSHARE = 3
    REVEAL = 3
    PRIVATE = 3
    FINAL = 3

BLOCK_TIME = 4
ROUND_DURATION = 3