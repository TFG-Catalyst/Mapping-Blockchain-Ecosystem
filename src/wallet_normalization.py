"""
Single definition of how the `voter` field of votes.csv is turned into a
wallet address. data_cleaner.py, explore_shared_voters.py and
shared_voters.py all use this function, so the voter identity is the same
in every part of the pipeline.

It has no dependencies, so it can be imported from scripts that do not use
pandas.
"""


def extract_address(voter_raw):
    """
    The `voter` field has a DIFFERENT format depending on the platform
    (checked with a real sample from each one):

    - aragon:            "<deployment_id>-voter-<address>"
    - daohaus/daostack/
      snapshot:          "<address>" (already given directly)
    - tally:             "eip155:<chain_id>:<address>" (CAIP-10 prefix)
    - realms:            Solana address in base58 (NOT 0x format,
                         it is case-sensitive, it must not be touched)

    We lowercase ONLY Ethereum-style addresses (0x...), because they are
    case-insensitive (checksum). Non-0x addresses (e.g. Solana on realms,
    or Tally's "solana:<network>:<address>") are left as they are so as not
    to corrupt the identity.
    """
    voter_raw = voter_raw.strip()

    # Format "<deployment_id>-voter-<address>"
    marker = "-voter-"
    position = voter_raw.find(marker)
    if position != -1:
        address = voter_raw[position + len(marker):].strip()
        if address.startswith("0x"):
            return address.lower()
        return address

    # Format "eip155:<chain_id>:<address>"
    if voter_raw.startswith("eip155:"):
        parts = voter_raw.split(":")
        address = parts[-1].strip()
        if address.startswith("0x"):
            return address.lower()
        return address

    # Plain Ethereum address
    if voter_raw.startswith("0x"):
        return voter_raw.lower()

    # Not a known 0x format (e.g. Solana address from realms): do not touch.
    return voter_raw
