 1. First, build the image. Make sure you are in the same directory as the docker file
```bash
docker image build -t dns-spoofer-target .
```
 
 2. Then, find the image using 
```bash
docker image list
```
and looking for the one with the tag dns-spoofer-target. 

3. Copy that image's id and run
```bash
docker run -it <your-image-id>
```
this will give you a shell inside the container if you want to execute DNS queries (for example using dig)

4. To actually find how to access this container, run the following command
```bash
ip link show type veth | grep docker
```
if there are multiple veths that show up, stop any other docker containers you have running and try again. The line should look something like
```shell
35: vethecbad69@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master docker0 state UP mode DEFAULT group default 
```
The part of the line that says ``veth...`` is the interface name associated with your container. This does not include the @ symbol and anything after it. So in the above case, it would be ``vethecbad69``.

5. If you need to find the local ip address associated with your container, go inside your container and run
```bash
ip addr show
```
You should see two interfaces, lo and eth0. Copy the inet address of the eth0 interface. See the example below
```bash
1: lo: 
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0@if35: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether a6:15:ce:73:e5:2f brd ff:ff:ff:ff:ff:ff link-netnsid 0
	# This is the line with the ip address you should grab
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever
```
Here the ip address associated with the container is ``172.17.0.2``, note that i excluded the subnet part ``/16``. Also note this is a local ip address, it will only work on the same computer as your docker container is running.

6. Now you can capture traffic coming from the container by using the veth interface and ``wireshark`` or ``tcpdump`` and you can send traffic by sending it to the local ip you found.



The above commands run on a Linux host. You should be able to set up the Docker on Windows/macOS using similar commands.

Some useful links:
- https://docs.docker.com/engine/network/drivers/bridge
- https://docs.docker.com/reference/cli/docker/inspect

Please start by setting up the Docker, identifying its IP address/interface, and capturing the traffic using network monitoring tools.
