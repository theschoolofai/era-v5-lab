 Queue and Partition Design
Slurm partitions represent logical job queues with configurable resource boundaries and scheduling policies.
Team 7 will implement two primary partitions: debug and train.
3.1 Partition definitions
Parameter
debug
train
Purpose
Diagnostics, smoke tests, troubleshooting
Full training and longer experiments
Maximum wall time
30 minutes
48 hours
Default wall time
10 minutes
4 hours
Maximum GPUs per job
1 (proposed policy)
8
CPU allocation
Small, controlled requests
Workload-dependent
Memory allocation
Small, controlled requests
Workload-dependent
Priority
Higher short-job partition factor
Standard partition factor
Preemption
Disabled initially
Disabled initially
User access
Authorized development users
Authorized training users
Primary goal
Quick turnaround
Efficient training throughput
Important scheduling distinction: Partition priority does not guarantee immediate execution. A pending debug job cannot
automatically displace a running training job unless an explicit preemption policy is enabled.
For the initial production deployment, disabling preemption avoids interrupting expensive training jobs. Debug responsiveness
will depend on resource availability, backfill scheduling, and optionally reserved resources.
3.2 Resource allocation policies
All users must declare their expected resource consumption. The scheduler should not allocate more resources than
requested, and jobs should be constrained to their allocated resources using the appropriate task and cgroup plugins.
For example, a production training job requesting four GPUs should not be able to consume or access GPUs allocated to
another job.
Resource requirements are evaluated using:
• CPU cores: --cpus-per-task, --ntasks
• Memory: --mem or --mem-per-cpu
• GPUs: --gres=gpu:N or an appropriate Slurm GPU request option
• Runtime: --time
• Partition: --partition
• Account: --account, if accounting associations are enforced
3.3 Shared-node partition behavior
On a single 8-H100 server, both debug and train partitions may reference the same physical node.
This means the partitions provide different policies but do not create physically independent resources.
A training job that allocates all eight GPUs can prevent a new debugging job from starting, even if the debug partition has a
higher priority factor.
For strict debug availability, Team 7 must either reserve appropriate resources, use a deliberate preemption strategy, or
introduce separate debug hardware.
The recommended initial model is a shared node with fair-share scheduling and backfill, accepting that debug jobs may
occasionally wait