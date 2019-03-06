# YASCO - Yet Another Static Cluster Orchestration

Orchestration of virtual machine with [libvirt](https://libvirt.org/) &amp;
[etcd](https://github.com/etcd-io/etcd) &amp; [ceph](http://docs.ceph.com/docs/master/).

## Table Of Content

[TOC]

## Preface

This is moment, when you are studying [SNE](https://os3.su/), doing Virtual Machine
Management lab with Cloud Orchestration. But it is the last night before deadline,
And figuring out the other monsters orchestration systems is too late, and I'm doubting
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

## The Cluster Knapsack problem

*Note: Here is the more mathematical definition of the problem, which I realized at 5:23 AM. In the next section there is more explainable definition of the problem.*

**We have:** set of virtual machines (`VMs`) and set of hardware machines (`HWM`),
which combined into cluster. We want to distribute VMs among the cluster with
two criteria quality:

1. Valid, the resources of `HWM` is more than sum of occupying resources placed `VMs`
2. Optimal, here a little bit difficult to define. But for example, we want to reduce
amount of HWMs to reduce power consumption.

The solution of the Cluster Knapsack problem is embodied by Cluster Distribution
Map (CDM, or CD Map), which describe the place each `VM_i` in the the `HWM_j`.

It is worth to mention, to each machine (hard or virtual) is at least 5-dimensions
cube `(RAM, Storage Size, CPU time, NetRX, NetTX)`. And it is right to start from
one dimension and define induction function over increasing dimensions. Because
during cluster maintenance we can add statistic-based dimensions to optimize
cluster experience.

That the simplest basis for optimal cluster configuration, but there are variations
of the problem:

1. High Availability problem (HA). We want to some defined subset of `VMs`
are working even if `X` hardware nodes has been failed. To do this we should
provision spare space in the cluster for evacuated `VMs` from fault nodes.

Here, we add to CD Map the fault redistribution maps for case that some subset
of HWM are failed. It is desired to calculate them in advance to be able to make
optimal orchestration decision right way.

There we can find some guesses about problem solvability: the set of subsets of
failed `HWM` with size less than `X` looks like Boolean, which means NP problem
with memory if we want to precalculate all fault redistribution maps in advance.

2. Another problem: the cluster users often do not utilize all VM resources
during long time. So, it is worth to define a convolution function of CDM to
place `VMs` on the less amount of `HWM`. And switch other freed `HWMs` to reduce power
consumption.

3. We need to understand that during cluster maintenance both sets (`VMs` and `HWMs`)
are changing. So we need optimal redistribution algorithm to migrate from old
CD Map to new CD Map.

It is really looks like [Ceph's CRUSH algorithm](https://vk.com/away.php?to=https%3A%2F%2Fceph.com%2Fwp-content%2Fuploads%2F2016%2F08%2Fweil-crush-sc06.pdf&cc_key=)
with different input conditions.

4. The last one problem, I guess, solving with previous task context: depending
on application high load we wants to change amount of `VMs` of the particular
application. It may be as increasing under High Load, but also decreasing
when High Load is gone.

## Problem definition (first version)

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

It is PoC for simple engine if we can solve the Cluster Knapsack problem. For
3 node I can defined it manually.

### Dump cluster VMs configuration

```bash
virsh dumpxml freebsd-vmm2 > freebsd-vmm2.xml
virsh dumpxml win7-vmm2 > win7-vmm2.xml
virsh dumpxml test > test.xml
virsh dumpxml ubuntu-vmm2 > ubuntu-vmm2.xml
cp *.xml domains/
```

## License

According to treatments about Results of Intellectual Activity, this is owned by
the [Innopolis University](https://university.innopolis.ru/en/). As author
I would like to make this work public under GPLv2.

I will be glad to know if you would like to publish this work in scientific
journals, because, I believe, there will be a lot of article to find optimal
solutions of defined Cluster Knapsack problem

## References

- [SNE](https://os3.su/)
- [asciiflow](http://asciiflow.com/)
- [DO: How To Create a High Availability Setup with Heartbeat and Floating IPs on Ubuntu 14.04](https://www.digitalocean.com/community/tutorials/how-to-create-a-high-availability-setup-with-heartbeat-and-floating-ips-on-ubuntu-14-04)
- [etcd](https://github.com/etcd-io/etcd)
- [CephFS](http://docs.ceph.com/docs/master/cephfs/)

## History notes

- Preliminary whiteboard discussion:

![](images/whiteboard-concept.jpg)

- It is one night repository. Such a lovely blizzard outside the Innopolis University:

![](images/morning.jpg)

- That moment, when you decide to shortly explain the problem to math friend, but instead of it
made the math problem definition and have to corrupt HTML page with dev-tools to make a good screenshot:

![](images/2019-03-06-math-friend.png)
