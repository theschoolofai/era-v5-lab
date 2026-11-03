"""KE2 (Kronecker embedding) toolkit for teams/04-ke2.

Modules
-------
config        pinned identities (tokenizer, upstream codec) and team paths
hashing       SHA-256 helpers shared by every artifact
upstream      locating the upstream ``kronecker_embeddings`` package
tokenizer     loading a byte-level BPE tokenizer and recovering exact token bytes
truncation    the named cut-to-P rules (upstream, proposed, table builder)
tables        the decode and raw per-token byte tables, with their integrity contract
script_class  script classes of token bytes, for collision reports
codec         the forward codec: upstream float32 wrapper and a float64 reference
"""

__version__ = "1.0.0"
