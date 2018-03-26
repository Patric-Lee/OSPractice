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
