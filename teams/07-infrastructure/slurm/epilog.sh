#!/bin/bash
# Slurm Epilog: free this node's restore staging area, so the next job has its NVMe space.
# Committed checkpoints on NVMe are kept (last 2) for a fast restore on the same node.
rm -rf /nvme/ckpt/*/restore 2>/dev/null
exit 0
