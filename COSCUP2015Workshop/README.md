COSCUP 215 Workshop
====

### 用途/What is this?：

三個檔案是在 COSCUP 2015 Open network Workshop 中所使用，功能分別是：

These files are used in COSCUP 2015 Open network Workshop, functions of

these apps are:

1. simple hub
2. packet in analyzer
3. routing

### 用法/How to use?：

只需使用 ryu-manager 啟動即可，要注意的是 route app 需要啟動 lldp 功能才可以正常運作

``` shell
 ryu-manager --observe-links [App name]
```
