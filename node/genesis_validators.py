from crypto.private import Private
from chain.params import GENESIS_VALIDATORS_COUNT

# super global list of genesis validators
# do not write in this arrays from outside
# to be replaced by real genesis validators in production
# only public keys will be known tp everyone


class GenesisValidators:
    private_keys = []
    public_keys = []

for i in range(GENESIS_VALIDATORS_COUNT):
    priv = Private.generate()
    pub = Private.publickey(priv)
    GenesisValidators.private_keys.append(priv)
    GenesisValidators.public_keys.append(pub)