# Two Controller

#### 如何使用？/How to use?

設定兩台 Controller

Setup two controller

``` python
two_controller.py:18 c0 = RemoteController('c0', '127.0.0.1', 6633)
two_controller.py:19 c1 = RemoteController('c1', '127.0.0.1', 6632)
```



然後直接執行即可

And run the script

``` shell
chmod +x ./two_controller.py
sudo ./two_controller.py
```