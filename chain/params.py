from enum import IntEnum, auto

class Round(IntEnum):
    PUBLIC = 0
    SECRETSHARE = 1
    PRIVATE = 2
    COMMIT = 3
    REVEAL = 4
    FINAL = 5
    INVALID = 6

#in blocks
class Duration():
    PUBLIC = 3
    COMMIT = 3
    SECRETSHARE = 3
    REVEAL = 3
    PRIVATE = 3
    FINAL = 3

BLOCK_TIME = 4
ROUND_DURATION = 3