Network Consistency Container
#############################

An easy way to maintain network policy consistency.

Installation
============

.. code-block:: bash

    $ pip3 install -r requirements.txt
    $ python3 setup.py install

Try it out
==========

Start an OpenFlow controller (assume the OpenFlow server is listen on
"192.168.1.21:6633").

Start the proxy on your proxy server with debug mode enabled (assume the server
ip is "192.168.1.22") to forward the traffic to the OpenFlow controller.

.. code-block:: bash

    $ python3 test/proxy_test.py -p 9090 --forward 192.168.1.21:6633 -v

Start the mininet to connect to the proxy:

.. code-block:: bash

    $ sudo mn --controller=remote,ip=192.168.1.22,port=9090
