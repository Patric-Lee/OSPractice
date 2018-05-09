## 容器通信的网络处理过程

### 同一host上同一子网内的两容器
我们称这两个容器分别为A和B，它们以桥接的方式连接在同一个虚拟的bridge上。A希望向B发送一个数据包。

A首先发出一个ARP请求，查找B的IP地址对应的MAC地址。虚拟的桥把这一请求向除了发来端口外的
所有端口广播，并收到与B连接的端口的ARP回复，从而桥设备知道了如何转发源为A终点为B的数据包。
接下来所有数据包都会由桥来进行转发。

值得注意的是两个容器的通信并不通过网关和真实的网卡。换言之，对网络管理员而言这些流量是透明的。

### 同一host上不同子网内的两容器
容器A发送数据包后，根据路由表数据包会发送给网关（在此之前A会先以ARP请求获取网关的MAC地址）。
数据包发送给A的网关后，网关判断并非同一子网，会向外传送数据包，经过外部网络（也包括主机）路由到达B的网关。
B的网关判断该数据包属于自己同一子网，因此广播ARP请求得到B的MAC地址，然后将数据包传给B。

### 通过gre隧道相连的两个host上同一子网内的两容器
容器A将数据包发送到隧道一端的路由器上，路由器通过地址判断数据包需要走gre隧道，因此进行封装（增加GRE header和新的IP header），然后传输新的封装好的数据包。
传输到隧道另一端的路由器上以后，路由器发现是GRE包且终点在可达范围内，进行解封（去掉新增的header），然后继续传输原始的数据包。

## VLAN技术的原理
VLAN，即VIRTUAL LOCAL ACCESS NETWORK（虚拟局域网）。我们知道，较近地理范围内一组计算机相互连通，
可以组成局域网，从而方便地共享文件、资源等。而VLAN则更进一步，它能够实现这样的效果：即使一组计算机在
物理上相距较远，甚至根本不在同一网段中，但逻辑上它们被组织起来，相互间的通信就像是在同一个局域网中一样。

相应地，VLAN也可以把原本在同一物理网段中的广播域逻辑上地划分为不同的广播域，控制不同用户间的互相访问。
例如，原本A、B两台设备连接在同一交换机上，C、D连在另一交换机上，两台交换机也相连接，那么当A发arp包请求
C的MAC地址时，所有的设备由于都在同一个广播域中，因此都会收到这一消息，从而造成浪费。现在我们把A、C划为
一个VLAN，B、D划为另一个VLAN，此时只有与A1同一个广播域的只有C了，从而减少了浪费。换言之，消息只会发给
同一个VLAN的设备。不同VLAN之间需要通信时，就需要路由器加以中继。

从上面可以看出，VLAN的技术关键在于两点：

其一，分隔不同VLAN，使不同VLAN的设备处于不同广播域中，同一VLAN的设备处于相同广播域中。
其二，实现不同VLAN间的通信。

我们分别来看如何实现这两点。

### 划分VLAN
VLAN中有两种连接：访问连接和汇聚连接。

访问连接连接的是VLAN的一个端口和一个客户端。该端口只属于一个VLAN。换言之，当客户端向该端口发送消息时，该端口只
向同一个VLAN的端口传输数据。确定端口VLAN的方法有很多，静态、动态，基于子网的、基于用户的都有。

汇聚连接连接的是两个物理交换机。这两个交换机上可能有多个VLAN，如果连接交换机的连接两端也只属于一个端口，容易造成端口的浪费，
同时布线也会十分复杂。因此汇聚连接的两端端口是所有VLAN公用的。进入汇聚连接前的数据包会被加上VLAN标签，标志着它属于哪一个VLAN，
在离开后标签会被去掉。这样就实现了连接的公用。主要的方法包括IEEE 802.1Q协议和ISL协议。

此外，如果不同VLAN之间需要通信，那么就需要路由器或是三层交换机进行路由。

### VLAN隔离的限制
基于IEEE802.1Q标准的协议中,TCI字段的12bit用来作为VLAN id的标识，因此VLAN的数量受此限制。加上两个保留的地址（0表示id为空，4095实现时保留为他用），VLAN隔离的数量最多为4094个。

## VXLAN和GRE技术的差异


## 实验
### 实验环境
安装有lxc的2.0.9版本的Ubuntu，内核4.4.0-62-generic

通过如下命令安装了openvswitch：
> sudo apt-get install openvswitch-switch

### 构建隔离的lxc容器集群
实验在两台服务器上共同完成：162.105.175.56和162.105.175.148.下面简称为服务器56和服务器148.

在服务器56上创建两个容器first和second。首先要更改lxc的配置：

更改$home/.local/share/lxc/[容器名]/config文件，增加两行指定网关和ip地址，更改一行指定联网设备为ovs桥。

例如，first容器的配置文件修改如下：

second容器配置文件修改如下：


然后运行脚本创建容器：
> lxc-create -n first -t download
> lxc-create -n second -t download

创建ovs的桥brv并启动：
'''
sudo ovs-vsctl add-br brv
sudo ip link set brv up

'''
接下来开启两个端口，保证host与容器能够互ping:
'''
sudo ovs-vsctl add-port brv firstport -- set interface firstport type=internal
sudo ovs-vsctl add-port brv secondport -- set interface secondport type=internal
sudo ip addr add 10.20.3.88/24 dev firstport
sudo ip addr add 10.20.2.88/24 dev secondport
sudo ip link set firstport up
sudo ip link set secondport up

'''

这之后才能启动容器，否则容器与主机无法ping通：
'''
lxc-start -n first
lxc-start -n second
'''

此时，键入这个命令可以看到目前的网络状态：

类似地，我们也在服务器148上创建桥、容器another：

由于我们还没有为端口分配tag，因此first与second可以互相ping。但一旦为它们分配了tag，两者就不再能够互相ping通。我们给anotherport和firstport
分配tag为1，给secondport分配tag为2,可以看到first仍能ping通another，而second不能了。

### 流量限制





