#!/bin/bash

export TOKEN=hohoho-and-bottle-of-beer
export CLUSTER_STATE=new
export NAME_1=ilya
export NAME_2=ayrat
export NAME_3=andreys
export HOST_1=10.0.0.112
export HOST_2=10.0.0.109
export HOST_3=10.0.0.127
export CLUSTER=${NAME_1}=http://${HOST_1}:2380,${NAME_2}=http://${HOST_2}:2380,${NAME_3}=http://${HOST_3}:2380
