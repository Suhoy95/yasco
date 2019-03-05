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
`n<X` HWMs are down. Let's call it Virtual Distributed Map (VDM).

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

## Solution in the real-life architecture context

I assume that cluster has general two-parts architecture: the virtual farm with
HWMs and distributed storage for easy migration and evacuation of HAVM instances:

```
                                    Internet
+---+-----------+-------------+---+    or
    |           |             |    Gateway(s)
+---+---+   +---+---+     +---+---+
|       |   |       |     |       |
| HWM_1 |   | HWM_2 | ... | HWM_K |
|       |   |       |     |       |
+---+---+   +---+---+     +---+---+
    |           |             |
+---+-+---------+-----------+-+---+ Internal
      |                     |       Network
+-----+---------------------+-----+
|                                 |
|       Distributed storage       |
|                                 |
+---------------------------------+
```

*Note*: it is really questionable is it worth to keep VM's images in
the distributed storage or not, while we assume that we have the static VDM and
do not plan to move VM instance to another node.

We will build our HA orchestration over already deployed study cluster:

```
+--------------------------------+   +-----------------------------+
|                                |   |                             |
| +--------------+ +-----------+ |   | +---------+ +-------------+ |
| |              | |           | |   | |         | |             | |
| | freebsd-vmm2 | | win7-vmm2 | |   | |  test   | | ubuntu-vmm2 | |
| |              | |           | |   | |         | |             | |
| +--------------+ +-----------+ |   | +---------+ +-------------+ |
|                                |   |                             |
|  HVM_1 Ilya's node (QEMU/KVM)  |   |HVM_2 Ayrat's node (QEMU/KVM)|
+-----------------+--------------+   +------------+----------------+
                  |                               |
                  +----------------+--------------+
                                   |
                 +-----------------+-----------------+
                 |                                   |
                 | +-------+   +-------+   +-------+ |
                 | |       |   |       |   |       | |
                 | | ceph1 |   | ceph2 |   | ceph3 | |
                 | |       |   |       |   |       | |
                 | +-------+   +-------+   +-------+ |
                 |                                   |
                 |  HVM_3 Andrey's node (QEMU/KVM)   |
                 +-----------------------------------+
```

Currently I am not consider the real VMs and HVMs resources. We want to all VMs
be a HAVM. Andrey's cluster node is considered as absolutely stable (it should
be bare-metal CEPH fault tolerance cluster).

For administration purpose, we place that map and VM configuration to dedicated
CephFS. And deploy `etcd` on each HVM node to keep state of cluster in quorum
and maintain it during work.

In that situations there are two evacuation distributions:

1. Ilya's node fail:
    - `Ayrat's node`: `test`, `ubuntu-vmm2`, `freebsd-vmm2`, `win7-vmm2`
2. Ayrat's node fail:
    - `Ilya's node`: `test`, `ubuntu-vmm2`, `freebsd-vmm2`, `win7-vmm2`

*Note*: it is possible to take in consideration also Andrey's node. But I do not
want to HAVMs influence to the ceph cluster, because they highly depended on it.
And also we did not set up migrations ability between (Ayrat's node and Andrey's
node) and (Ilya's node and Andrey's node).

**Task**: write python daemon for Ilya's and Ayrat's nodes, which will pool the
`etcd` to keep track of cluster state, perform node evacuation and migrate the
HAVMs after node rescue.

### Solution notes

*Note 1*: cluster administrators have another problem of poor utilizing the cluster,
because VMs often do not utilize its resources, and you can have low-load nodes.
To facilitate it, for example, memory ballooning is used, or just put more VMs to
the HVM. This approach is tricky as soon as the cluster provider can provide more
virtual resources than it really has. The problem definition made to avoid that
situation. You can go further, and try to define Virtual Distribution Map wrapping
depends on the Cluster usage statistic to move some HAVM and VM to other HWM, and
shutdown several HVM nodes while you do not have a high-load.

*Note 2*: During exploitation some applications (VMs) are wanted to be vertical
scaled depends on load. It means that we need several Cluster Distribution Maps
which will change depending on situation. We do not consider that case currently.

*Note 3*: Other problem will be when we will add or remove VMs and HAVMs. It is
pretty looks like re-balancing problem solved by CRUSH algorithm (CEPH). I think
it could be solved in similar passion. At least in the worst case scenario, we
can just calculate new CDM, and remigrate whole cluster, which will be horrible
in a big scale.

*Note 4*: It reminds me the web-page evolution: in the beginning we had static
document HTML pages, then started to generate WEB-application with MVC application,
and then realized that we can take the template library and generate a static pages
and avoid calculations on each page. Here the same way: for lite-middle size cluster
we can pre-define VMs distribution, and also fault tolerances strategies for HA.
After that the yasco daemon just need to monitor the current cluster state and
apply the CDM depends on situation.

## Proof-Of-Concept

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
