# Lab 2 报告

## Rootfs制作流程

本次选看的是Ubuntu的rootfs制作脚本，安装lxc后位于/usr/share/lxc/templates文件夹下，文件名为lxc-ubuntu。


制作流程如下所示：

* 给参数赋值
> 包括release（版本）、arch（体系结构）、hostarch（宿主机体系结构）、user、password等等。


* 确认debootstrap命令存在，确认脚本在root下运行，检查配置路径中是否已经存在rootfs
> debootstrap是ubuntu构造根文件系统的命令，稍后会调用

* 调用install_ubuntu函数
> * 加锁，防止进程意外退出造成问题
> * 在参数cache和arch指定的路径下清除原有的/partial-$arch和/rootfs-$arch文件夹，安装首先在前一个文件夹中进行，
根文件系统制作的工作完成后才复制到后一个文件夹
> * 检查有无cache存储的ubuntu文件，如果没有，调用download_ubuntu

>>  * 配置镜像路径、语言、需要的package等参数
>>  * 为了防止以外退出造成的文件残留，这里利用trap命令指定收到某些中断信号时进行清理工作

>>  * 建立/partial-$arch文件夹

>>  * 为容器选择代理（squid），用于加快下载
>>  * 使用qemu-debootstrap命令和debootstrap命令安装根文件系统

>> * 在新建立的该容器的根文件系统中更改源列表并进行更新
>> * 挂载容器的根文件系统下的/proc，并使用lxc-unshare命令隔离它与宿主的文件系统
>> * 把在/partial-$arch中建立好的根文件系统直接拷贝到/rootfs-$arch下



> * 调用copy_ubuntu函数，把已经建立好的根文件系统拷贝到参数rootfs指定的路径中，也就是真正的根文件系统应该在的路径

>> 这里对btrfs文件系统做了单独的处理

* 调用configure_ubuntu函数
> * 利用dhcp配置网络
> * 设置用户、密码、语言、所在地
> * 生成新的SSH密钥

* 调用copy_configuration函数，主要是进行配置文件中路径的重定位以及添加该容器的特定配置

* 调用post_process函数
> * 处理体系结构与宿主机相同以及不同的情况
> * 在容器内安装必要的软件包，设置时区

* 调用finalize_user函数，将之前生成的SSH密钥与用户关联起来


## fakeContainer实验
### 实验环境
Ubuntu 16.04.2
内核版本为4.4.0-62-generic
体系环境x86_64
lxc 2.0.9

![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/CPU_info.JPG)

如图所示可知机器有两个单核逻辑CPU，也是两个物理CPU。


Ubuntu对于cgroup的相关配置在目录/sys/fs/cgroup下。

### 内存压力测试
观察Ubuntu在目录/sys/fs/cgroup下的文件可以看到，文件memory.limit_in_bytes用于限制内存使用，因此我们加入如下代码：

```
 struct cgroup_controller *cgc_cpumem = cgroup_add_controller(cgroup, "memory");
    if ( !cgc_cpumem) {
	ret = ECGINVAL;
	printf("Error add controller %s\n", cgroup_strerror(ret)); 
	goto out;
    }

    if ( cgroup_add_value_uint64(cgc_cpumem, "memory.limit_in_bytes", 512*1024*1024)) {
    	printf("Error limit cpumem memory.\n");
	goto out;

    }
```

内存测试的脚本如下（不断将字符串长度翻倍，这里为了便于观察，每次翻倍后休眠1秒）：

![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/mem_test_sh.JPG)

利用free指令我们可以发现，在内存被耗光以后，进程暂时没有被杀死，swap分区的使用逐渐增加，
增加到一定程度后就保持在一定数值不动。

![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/mem_test_res_1.JPG)
![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/mem_test_res_2.JPG)
![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/mem_test_res_4.JPG)



此时利用ps查看进程，发现它处于D状态，也就是休眠状态。

![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/process_state.JPG)


但再经过一段时间，容器内会有如下的显示：

![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/mem_test_kill.JPG)

此时进程已经退出。

但如果我们使用swapoff命令关闭swap分区，进程内存超出限额后马上会被杀死：


![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/swap_off_res.JPG)


### CPU压力测试
相应地，我们把cpuset.cpus的值改为“0”，即可达到限制CPU使用的结果。

CPU压力测试的脚本如下（执行一段死循环）：

![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/cpu_test_sh.JPG)

利用top指令（键入“1”）我们可以看到确实只使用了一个CPU核。
运行脚本前：

![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/Before_cpu_test.JPG)

运行脚本时：

![image](https://github.com/Patric-Lee/OSPractice/blob/master/Lab2/pic/cpu_test.JPG)



## 与LXC的对比
fakeContainer中没有init等操作系统的基本进程，还不能模拟完整的操作系统。例如
在fakeContainer中，我们是无法使用sudo的，否则会提示：
> sudo: /usr/bin/sudo must be owned by uid 0 and have the setuid bit set.

而在lxc中，我们可以使用sudo。这会影响我们对一些系统命令的使用。



此外，从宿主访问fakeContainer的方法只有一种，而在lxc中，我们可以通过lxc-attach在容器内执行命令，或者是通过网络的方式进行通信。

因此，要想改善该lab，我们可以尝试：
完整模拟操作系统的启动过程，在运行了init等进程的基础上再运行shell；
提供更多方便的交互方式，如实现lxc-attach命令；
实现容器自己的网络栈，提供host与容器互相通信的方法。




