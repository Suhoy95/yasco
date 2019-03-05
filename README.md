# YASCO - Yet Another Static Cluster Orchestration

Orchestration of virtual machine with [libvirt](https://libvirt.org/) &amp;
[etcd](https://github.com/etcd-io/etcd) &amp; [ceph](http://docs.ceph.com/docs/master/).

## Table Of Content

[TOC]

## Preface

This is moment, when you are studying [SNE](https://os3.su/), doing Virtual Machine
Management lab with Cloud Orchestration. But it is the last night before deadline,
And figuring out the other orchestration systems is too late, and I'm doubting
about its design and clearness. So It is better to use brute force and
DO IT YOURSELF with python.

![](https://4.bp.blogspot.com/-iy-_fn5n-ZI/V2IVw34C8YI/AAAAAAAAlHE/tXUlW2AYnqYwVgsjKikqqu8SvnGoKxMtwCLcB/s640/may-the-force-be-with-you.JPG)

Generally, we wants solve with orchestration two problems:

- Automatic high available resolving (i.e. evacuating VM instances)
- Efficient cluster utilizing (i.e. returning the VMs to its home, when the fail
node has been recovered)

During preliminary discussion the idea has transformed from old-school bash script
with [heartbeat](https://www.digitalocean.com/community/tutorials/how-to-create-a-high-availability-setup-with-heartbeat-and-floating-ips-on-ubuntu-14-04)
to using distributed database to keep consensus state, like [etcd](https://github.com/etcd-io/etcd),
and [CephFS](http://docs.ceph.com/docs/master/cephfs/) to distribute the VM configurations
among the cluster.

*Note*: written in defining idea first approach.

## Problem definition

Suppose, we have virtual machines farm. And we should manage `N` plain
Virtual Machines (VM), `M` High Available Virtual Machine (HAVM) and
`K` Hardware Machines:

```
+------+   +------+       +------+
| VM_1 |   | VM_2 |  ...  | VM_N |
+------+   +------+       +------+

+--------+   +--------+     +---------+
| HAVM_1 |   | HAVM_2 | ... | HAVM_M  |
+--------+   +--------+     +---------+

+---------+   +---------+     +---------+
|         |   |         |     |         |
|  HWM_1  |   |  HWM_2  | ... |  HWM_K  |
|         |   |         |     |         |
+---------+   +---------+     +---------+
```

Before running this set up we know amount of resources required by each VM node
and amount of available physical resources provided by all hardware machines.
Approximate set of that resources: RAM, CPU power, Hard Drive Space, RX/TX
network throughput.

**Problem**: we wants to distribute these VMs and HAVMs among the cluster to be
able to guarantee that HAVM will be available even with `X` crushed hardware
machines. In other words, we want to split HWM into `Y` spare slots, each of them
will be correspond one of VM or HAVM, and also several free slots for HAVMs if
`n<X` HWMs are down.

```
             +------+                 +------+                        +------+
             | VM_1 |                 | VM_2 | ...   ...    ...   ... | VM_n |
             +--+---+                 +---+--+                        +---+--+
                |                         |                               |
  +--------+    |          +--------+     |           +--------+          |
  | HAVM_1 |    |          | HAVM_2 | ... | ...   ... | HAVM_m |          |
  +---+----+    |          +---+----+     |           +----+---+          |
      |         |              |          |                |              |
+----------------------+ +----------------------+     +-------------------------------+
|     |         |      | |     |          |     |     |    |              |           |
| +---v---+  +--v----+ | | +---v---+  +---v---+ |     | +--v----------+ +-v---------+ |
| | slot1 |  | slot2 | | | | slot3 |  | slot4 | |     | |             | |           | |
| +-------+  +-------+ | | +-------+  +-------+ |     | | slot(n+m-1) | | slot(n+m) | |
|                      | |                      | ... | |             | |           | |
|    +-------------+   | |    +-------------+   |     | +-------------+ +-----------+ |
|    | spare slot1 |   | |    | spare slot2 |   |     |         +-------------+       |
|    +-------------+   | |    +-------------+   |     |         | spare slotY |       |
|                      | |                      |     |         +-------------+       |
|        HWM_1         | |        HWM_2         |     |             HWM_K             |
|                      | |                      |     |                               |
+----------------------+ +----------------------+     +-------------------------------+
```

TODO: relation between `X`, `Y` and `M`. It is also required to define all resources
which we want to take into account.

*Note*: Why do we need the difference between VM and HAVM? Some services are not
so critical and can accept 3-10 minutes downtime of rebooting the dedicated HWM
in case of failure. For example, landing pages or static documentation web sites.
This differentiation allows reduce amount of spare slots required to evacuating
HAVMs from failed HWM. You should understand that each spare slot is just
resources which **you have, but do not use**, because of provisioning purposes.

*Note*: The problem looks like [Knapsack problem](https://en.wikipedia.org/wiki/Knapsack_problem),
but as more general case. Currently, I am not solving this problem, but create
a PoC which uses its solution to handle HA requirements.

## Theoretical real-life solution



### Solution notes

TODO Note: problem of low-usage of virtual machines

TODO Note: problem of vertical virtual machine scale

TODO Note: problem of re-balancing

## Related works parallels

## Proof-Of-Concept

### Predefined Cluster Setup

### Architecture

### Implementation

### Demonstration

## References

- [SNE](https://os3.su/)
- [asciiflow](http://asciiflow.com/)
- [DO: How To Create a High Availability Setup with Heartbeat and Floating IPs on Ubuntu 14.04](https://www.digitalocean.com/community/tutorials/how-to-create-a-high-availability-setup-with-heartbeat-and-floating-ips-on-ubuntu-14-04)
- [etcd](https://github.com/etcd-io/etcd)
- [CephFS](http://docs.ceph.com/docs/master/cephfs/)

## History notes

- Preliminary whiteboard discussion:

![](images/whiteboard-concept.jpg)
