#!/bin/bash
# Accounts, QOS and limits in slurmdbd (ADR 0002 §4). Safe to run twice.
#
# In simple words: the main run has its own account with top priority and may take nodes from anyone.
# Every team has its own account under "teams"; they share the rest fairly, each has a GPU share and a node
# cap so no team can take everything, and each has a GPU-hour budget so nobody overspends.
# Team jobs have a time limit (longer work requeues itself, see team_job.sbatch) and a cap on queued jobs; a
# "debug" QOS gives one quick 1-GPU job ahead of the queue. Limits from Max's queue design, GPU shares from
# Mallik's accounts (team 07). On one shared 8-GPU node set V5_NODE_CAP high and V5_TEAM_GPUS to TSAI's share.
set -u
S="sacctmgr -i"
TEAM_GPUS="${V5_TEAM_GPUS:-16}"          # GPUs one team may hold at once (EC2: 2 nodes x 8)
NODE_CAP="${V5_NODE_CAP:-2}"             # nodes one team may hold at once
TEAM_MAXWALL="${V5_TEAM_MAXWALL:-24:00:00}"
TEAM_MAXSUBMIT="${V5_TEAM_MAXSUBMIT:-50}"  # queued + running jobs per team
# DenyOnLimit: a job over a per-job limit is refused at submit with the reason, instead of pending forever.
$S modify qos normal set Priority=10 GraceTime=60 MaxWall="$TEAM_MAXWALL" MaxTRESPerJob=gres/gpu="$TEAM_GPUS" \
  MaxSubmitJobsPerAccount="$TEAM_MAXSUBMIT" Flags=DenyOnLimit
$S add qos debug >/dev/null 2>&1
$S modify qos debug set Priority=100 GraceTime=30 MaxWall=00:30:00 MaxTRESPerJob=gres/gpu=1 MaxJobsPerUser=1 \
  MaxSubmitJobsPerUser=2 Flags=DenyOnLimit
# After the QOS it preempts exist: sacctmgr rejects the whole Preempt list if one name is unknown, and the main
# run then waits for free nodes instead of taking them (found by the preemption drill, run 15).
$S add qos mainrun >/dev/null 2>&1
$S modify qos mainrun set Priority=1000 Preempt=normal,debug PreemptMode=requeue
pre=$(sacctmgr -n -P show qos mainrun format=preempt)
[[ "$pre" == *normal* && "$pre" == *debug* ]] || { echo "setup_accounts: mainrun Preempt is '$pre', expected normal,debug" >&2; exit 1; }
$S add account mainrun Description="V5 main run" Organization=v5 >/dev/null 2>&1
$S add account teams Description="all teams" Organization=v5 >/dev/null 2>&1
TEAMS="data tokenizer ke2 arch perf infra monitoring eval posttrain release quant"
for t in $TEAMS; do
  $S add account "$t" parent=teams Fairshare=1 Organization=v5 >/dev/null 2>&1
  $S modify account "$t" set GrpTRES=node="$NODE_CAP",gres/gpu="$TEAM_GPUS"
done
# The submit service user is the only user; the account it passes decides who pays.
$S add user svc Account=mainrun DefaultAccount=arch >/dev/null 2>&1
for t in $TEAMS; do $S add user svc Account="$t" >/dev/null 2>&1; done
$S modify user svc where account=mainrun set QOS=mainrun,normal DefaultQOS=mainrun
for t in $TEAMS; do $S modify user svc where account="$t" set QOS=normal,debug DefaultQOS=normal; done
# root runs the retention and export jobs in the test (on AWS: their own IAM roles, ADR 0002 §7).
$S add user root Account=infra DefaultAccount=infra >/dev/null 2>&1
$S modify user root where account=infra set QOS=normal DefaultQOS=normal
sacctmgr -n -P show assoc format=account,user,qos,grptres | sort
