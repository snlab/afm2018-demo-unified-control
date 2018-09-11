#!/usr/bin/env python2.7

import sys, os

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from functools import partial

import subprocess

def demo_sc16(controller_ip):
    if controller_ip == '127.0.0.1':
        net = Mininet(switch=OVSKernelSwitch, link=TCLink)
        ctl = net.addController("c1")
    else:
        net = Mininet(controller=RemoteController, switch=OVSKernelSwitch, link=TCLink)
        ctl = net.addController("c1", controller=RemoteController, ip=controller_ip)


    l1 = net.addHost("l1", ip='10.0.0.2', mac='12:34:56:78:90:02')
    l2 = net.addHost("l2", ip='10.0.0.3', mac='12:34:56:78:90:03')
    l3 = net.addHost("l3", ip='10.0.0.4', mac='12:34:56:78:90:04')

    dpi = net.addHost("dpi", ip='10.0.1.1', mac='12:34:56:78:91:01')

    r1 = net.addHost("sci", ip='10.0.2.2', mac='12:34:56:78:92:02')
    r2 = net.addHost("cas", ip='10.0.2.3', mac='12:34:56:78:92:03')

    building = net.addSwitch('building', dpid='1', protocol='OpenFlow13')
    campus = net.addSwitch('campus', dpid='2', protocol='OpenFlow13')
    firewall = net.addSwitch('firewall', dpid='3', protocol='OpenFlow13')
    science = net.addSwitch('science', dpid='4', protocol='OpenFlow13')
    border1 = net.addSwitch('heborder', dpid='5', protocol='OpenFlow13')
    border2 = net.addSwitch('foborder', dpid='6', protocol='OpenFlow13')

    net.addLink(building, l1)
    net.addLink(building, l2)
    net.addLink(building, l3)

    net.addLink(firewall, dpi, bw=400)

    net.addLink(border1, r1)
    net.addLink(border2, r2)

    net.addLink(building, campus, bw=400)
    net.addLink(building, science, bw=1000)

    net.addLink(campus, firewall, bw=400)

    net.addLink(firewall, border1, bw=400)
    net.addLink(firewall, border2, bw=400)

    net.addLink(science, border1, bw=1000)
    net.addLink(science, border2, bw=400)

    net.build()

    ctl.start()

    building.start([ctl])
    campus.start([ctl])
    firewall.start([ctl])
    science.start([ctl])
    border1.start([ctl])
    border2.start([ctl])

    l1.cmd('export PATH=$PATH:/home/mininet/tutorial-sc16')
    l2.cmd('export PATH=$PATH:/home/mininet/tutorial-sc16')
    l3.cmd('export PATH=$PATH:/home/mininet/tutorial-sc16')
    dpi.cmd('export PATH=$PATH:/home/mininet/tutorial-sc16')
    r1.cmd('export PATH=$PATH:/home/mininet/tutorial-sc16')
    r2.cmd('export PATH=$PATH:/home/mininet/tutorial-sc16')

    os.system('/home/mininet/bro_http/start_bro.sh firewall-eth1 127.0.0.1')

    r1.cmd('demoserver 10.0.2.2 80 1>sci.log 2>/dev/null &')
    r2.cmd('demoserver 10.0.2.3 80 1>cas.log 2>/dev/null &')

    net.start()
    CLI(net)
    net.stop()

    os.system('pkill gunicorn')
    os.system('pkill bro')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: python {} [CONTROLLER_IP]".format(__file__)
        sys.exit()
    demo_sc16(sys.argv[1])

