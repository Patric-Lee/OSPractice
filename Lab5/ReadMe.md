## Raft协议工作场景及处理流程

### Raft工作原理
Raft是一个分布式系统的工作协议，目的是保证分布式系统的数据最终一致性，即：对于操作结果而言，分布式系统
各节点中数据的值是一致的。粗略地讲，Raft协议这样来实现数据一致性：

每个节点有三种状态：Leader，Follower和Candidate。

Leader向Follower发送命令，负责数据的更新；同时也会定期发送心跳讯息，以维持自己的Leader地位。
每一次数据操作都要通过Leader完成。

Follower接受Leader的指示更新数据并回复。当Follower失去与Leader联系时（即没有收到定期的心跳
讯息），如果满足一定条件，则成为Candidate并向其他所有节点发出竞选Leader的消息。

Candidate在得到过半数节点同意（即回复）的情况下成为新的Leader。

每次竞选Leader过程开启，就会产生一个新的任期。任期用一个连续的递增的整数表示。在一个任期内至多只有一个有效的Leader。这是通过
以下两点保证的：

如果原来的Leader宕机后又恢复了，但此时已经产生了新的Leader，那么旧Leader在收到新Leader信息时
比较任期，发现自己的任期较小，于是自动放弃Leader地位成为Follower。

如果有多个Candidate竞争，由于过半数才能成为Leader，因此保证了至多只有一个新Leader产生。若平票，那么
各个Candidate节点将在随机时间内重新发起投票，再次竞争。

每个节点各自维护一份数据日志。日志分为两部分：已经提交（committed）的部分和未提交的部分。Raft协议
保证已经提交的部分是已经被过半数节点写入的。通常一个数据操作是这样完成的：

客户端向系统请求操作数据，节点收到后转发给Leader；

Leader自身将该操作写入日志未提交部分，并广播给所有节点；

收到信息的节点将该操作写入日志未提交部分，并回复；

Leader收到过半数节点回复，将该操作的状态更改为已经提交，并广播给所有节点；

收到信息的节点也完成提交的工作。

值得注意的是，每个节点的数据日志必须是连续编号的，不允许有空缺，也不允许在已提交的日志之前还有未提交的
日志。

在上面的操作过程中随时可能出现Leader宕机的情况，这里不再细致讨论。

最后，Raft协议对于增减节点的问题没有特别完善的解决方案。一种可能的方法是，每次只允许增减一个节点，从而保证一个任期内仍然至多只有一个有效的
Leader。

### 工作场景举隅
Raft在etcd中得到了实现。ETCD是一个分布式的键-值存储系统，有许多工作场景。我们不妨来看ETCD中如何利用raft实现分布式锁的功能。

所谓分布式锁，就是分布式系统上的锁。最基础的分布式锁需要满足互斥的功能（即同一时间只能有一个客户端获取到锁），同时要能够被释放，不会造成最后的死锁。在etcd这样的分布式键-值存储系统中，我们
可以这样来实现分布式锁：
在存储系统中有一个单独与该锁相关的表。每个客户端在该表中创建一条记录，包含与自己相对应的key。key值最小的那个客户端获得锁。释放锁前删掉自己在表中的
记录，下一个key值最小的客户端获得锁。以此类推。

Raft协议在这里主要保证的是每个客户端创建记录和删除记录时的一致性。具体的过程如前所述，这里不再细谈。




## GlusterFS与AUFS
### GlusterFS及其特点
GlusterFS是一种分布式文件系统。它最大的特点就是没有元数据服务，数据的存储完全通过（散列）算法实现。此外，GlusterFS还有几个显著的特点：

扩展性强。能够支持PB级的存储容量和上千台客户端。

完全软件实现。独立于硬件和操作系统。

在用户空间中实现。利用了微内核的思想，方便了用户的使用和修改。

堆栈式的模块架构。

### GlusterFS的工作原理
用户访问GlusterFS上的文件时，要经历如下的流程：

首先，通过系统调用陷入内核，访问VFS；

VFS将访问或者数据操作交给内核FUSE文件系统，后者访问/dev/fuse设备来把数据传给GlusterFS的客户端；

GlusterFS客户端通过网络把数据发给服务器端并进行相应的操作。

参考资料

http://blog.51cto.com/dangzhiqiang/1907174

### AUFS及其工作原理
AUFS是一种联合文件系统，能够完成保持几个文件目录物理上分离的同时进行逻辑上合并的工作。每一个被合并的目录称为一个branch，AUFS支持
对每一个branch指定读写权限，通常至少有一个branch需要是可写的。AUFS的branch之间是一层一层地堆叠在一起的，任何访问只影响到最上层的满足条件
的branch。具体说来，

如果是读操作，那么从上层向下找到第一个拥有该文件的branch，返回这一branch的结果，其他branch的同名文件不影响返回结果；

如果是写操作，那么从上层向下找到第一个拥有该文件的可写的branch进行修改，其他branch的同名文件不受影响；

如果是创建新文件，那么根据参数选择一个可写branch进行创建；

如果是删除文件，如果可写branch中有该文件，那么直接删除，此外无论可写branch有无该文件，创建一个.wh开头的相应文件标明该文件已被删除，其他branch的
同名文件仍然存在。

## 配置GlusterFS
首先在两台服务器上分别安装GlusterFS server:
> sudo apt-get install glusterfs-server

创建相应的文件夹作为存储点，我们这里直接在$home下创建了/glus文件夹。
随后在一台服务器上运行，这里我选择了148服务器：
```
sudo gluster peer probe 162.105.175.56
sudo gluster volume create rep replica 2 162.105.175.56:/home/pkusei/glus 162.105.175.74:/home/pkusei/glus force
sudo gluster volume start rep
```
我们可以查看到glusterfs的状态：
![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab5/image/peer_probed.JPG)
![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab5/image/volume_created.JPG)

随后我们启动一台privileged container（否则无法mknod）.我们首先在其中创建fuse设备：
> mknod /dev/fuse c 10 229

然后安装gluster-client:
> sudo apt-get install glusterfs-client

注意，这里要保证client和server的版本相同。

然后我们就可以把rep挂载到容器中了：
>  sudo mount -t glusterfs 162.105.175.148:rep /home/ubuntu/data/

在容器内部向data文件夹写入文件。同时可以发现rep中也可以看到：
![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab5/image/mount_finished.JPG)

破坏一台服务器的数据，从容器内部也仍然能看到完好的文件。
![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab5/image/break_one_machine.JPG)

## 为LXC提供镜像服务

我们首先创建并启动两个容器：
```
lxc-create -n base -t download
lxc-create -n withPython -t download
lxc-start -n base
lxc-start -n withPython
```

其中选择Ubuntu trusty版本，体系结构为i386.这样启动的容器中是没有Python的。为了测试，我们在withPython中安装Python。

接下来，找到两个容器各自的rootfs分别为
```
$dir1=~/.local/share/lxc/base/rootfs
$dir2=~/.local/share/lxc/withPython/rootfs
```

使用aufs合并两个rootfs到test文件夹中，base作为可写branch：
```
sudo mount -t aufs -o dirs=$dir1:$dir2 none /home/pkusei/test
```

接下来我们创建一个新容器test，并修改它的config文件中lxc.rootfs一行为：
```
lxc.rootfs = /home/pkusei/test
```

启动test容器，会发现可以在test中运行Python：

![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab5/image/testAUFS.JPG)




















