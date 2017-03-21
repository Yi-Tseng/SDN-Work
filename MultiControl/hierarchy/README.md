Hierarchy SDN routing control for multiple domain
----

This project is the final project for SDN course in NCTU

Author:

Tseng Yi(a86487817[at]gmail.com)

naoh (kennynaoh[at]gmail.com)

## How to use with test environment (mininet):

1. Start global controller
```
$ python global.py
```

2. Modify global ip address in local controller (local.py#L31)
```python
self.local_lib.start_serve('127.0.0.1', 10807)
```

3. Start local controllers (example is 3), I suggest start from different bash session.
```
$ run1.sh # this start controller with port 6633
$ run2.sh # port 6634
$ run3.sh # port 6635
```

4. Modify controller ip addresses from mininet script (test_net.py#L17-L19)
```python
c0 = RemoteController('c0', '10.10.10.10', 6633)
c1 = RemoteController('c1', '10.10.10.10', 6634)
c2 = RemoteController('c2', '10.10.10.10', 6635)
```

5. Start mininet
```
# python test_net.py
```

