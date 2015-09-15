# Fat Tree

### 用途/What is this?：

用來產生 Fat tree 唾撲

For generating fat tree topology

### 用法/How to use?：

1.設定 Controller:

1.Setup controller:

``` python
fat_tree.py:158 net.addController('Controller', controller=RemoteController, ip='127.0.0.1', port=6653)
```

2.(選擇性的)設定：

- k 值
- Aggregation 到 Core 的頻寬
- Pod 內的頻寬
- Aggregation 到 Core 的封包遺失率
- Pod 內的封包遺失率

2.(Optional)setup:

- k value, bandwidth between aggregation and core(Default 1Gbps)
- bandwidth between switches in pod(Default 100Mbps)
- packet lost between aggregation and core(Default: 5%)
- packet lost between switches in pod(Default: 0%)

``` python
fat_tree.py:155 fat_tree = FatTreeTopo(k=4, ac_bw=1000, pod_bw=100, ac_pkt_lost=5, pod_pkt_lost=0)
```

3.執行 fat_tree.py

3.Start fat_tree.py

``` shell
chmod +x ./fat_tree.py
sudo ./fat_tree.py
```
