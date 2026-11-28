# Router comparison arms

The 28 Nov Lab 5 recipe requires every 2D matrix on Muon, with no SGD.
`router_muon.yaml` remains runnable under that recipe. Its input and head matrices
now also use Muon, so it does not reproduce the old comparison's grouping.

`router_adamw.yaml` was retired from the runnable arm tree: it selected Muon but
set `router_on_muon: false`, which now fails validation. Changing that flag to
`true` would silently change the named experiment. No new ablation flag is added.
TSAI requires a new explicit flag if a future named ablation needs an exception.

For historical reproduction, use the original arm **and matching trainer code**
from commit `83e98a6e1f94b70d7850f3205aa1b2fe4dddc6d9` (before the Lab 5 grouping
change). The dated job request and evidence under
`jobs/2026-11-21-router-comparison.md` and
`jobs/evidence/2026-11-21-router-comparison/` remain historical records; their
commands and manifests describe that earlier code, not current runnable arms.

The config sweep found no `head_sgd: true` settings. The remaining 25 arms pass
native config validation with `configs/small/smoke_resolution.yaml`.
