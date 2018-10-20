from enum import IntEnum

# initial number ov validators
GENESIS_VALIDATORS_COUNT = 20  # default 20
# steps/seconds per block
BLOCK_TIME = 4  # default 4
# blocks per round
ROUND_DURATION = 3  # default 3


class Round(IntEnum):
    PUBLIC = 0
    COMMIT = 1
    SECRETSHARE = 2
    REVEAL = 3
    PRIVATE = 4
    FINAL = 5
    INVALID = 6

SECRET_SHARE_PARTICIPANTS_COUNT = 3

MINIMAL_SECRET_SHARERS = ROUND_DURATION // 2 + 1
TOTAL_SECRET_SHARERS = ROUND_DURATION

ZETA = 5
ZETA_MIN = 3
ZETA_MAX = 5


# rounds length in blocks
#    PUBLIC = 3
#    COMMIT = 3
#    SECRETSHARE = 3
#    REVEAL = 3
#    PRIVATE = 3
#    FINAL = 3 + 1

