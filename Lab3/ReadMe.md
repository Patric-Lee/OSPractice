# Lab 3 实验报告
## Linux网络包处理流程
在外部网络和本机之间，Linux内核提供了netfilter机制作为防火墙，管理经过的网络数据包。
为了方便使用，又提供了iptables软件，使得用户可以在用户态下操纵netfilter。该图表现的就是
iptables的整体结构。

Iptables由四个表、五个链组成。其中，每个链代表一个关卡或是一个检查站，在不同的位置对网络数据包
根据规则进行检查并作出相应的操作。五个链分别为：
PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING.

相应的操作包括ACCEPT（允许数据包通过），DROP（忽略数据包）, REJECT（拒绝数据包并给源地址发拒绝消息）等。

由于不同的链中的规则可能完全相同，因此可以用表来将功能相似的规则组合在一起，这样只需要将表适用在不同链上即可，
而无需为某个链单独写规则。四个表分别为：
raw, mangle, nat, filter.

不同的表有不同的适用范围，即只在一定的链中起作用。如图所示，我们知道：

PREROUTING链中raw，mangle，nat表起作用；
INPUT链中mangle，filter表起作用；
FORWARD链中mangle，filter表起作用；
OUTPUT链中四个表均起作用；
POSTROUTING链中mangle，nat表起作用。

具体到数据包的流向，有三种可能：
第一，外部网络发给本机的数据包，经过PREROUTING和INPUT两个链；
第二，本机发给外部网络的数据包，经过OUTPUT和POSTROUTING两个链；
第三，外部网络发给外部网络路过的数据包，经过PRETOUTING，FORWARD和POSTROUTING三条链。

数据包按照指定的路径流向传送，依次经过各个链，并按顺序检查是否符合链中各个表下的规则适用范围，如果适用则
作出相应的操作。

## IPTABLES功能测试
### 拒绝来自某一特定IP地址的访问

### 只开放本机http和ssh服务，拒绝其余协议与端口

### 拒绝回应来自某一特定IP地址的ping命令

## 路由与交换
路由和交换都是指网络数据包在传颂过程中发生的转发操作，即从一个地址转发到另一个地址的过程。
二者都需要维护一个相当于map的地址表，查看目标地址所对应的端口。
不同之处在于，路由在网络层工作，它根据IP地址来进行查找定位；而交换在链路层工作，根据MAC地址来查找。

## Bridge与veth的工作原理

## 为fakeContainer增加网络功能
我使用了命令行脚本来完成这一任务。

## 访问容器内Nginx容器

## 处理流程


