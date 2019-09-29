# 鬼镜(ghostmirror)
鬼镜(ghostmirror)是一个通过webshell实现的**内网穿透工具**.工具主体使用python开发,当前支持php,jsp,aspx三种代理脚本.
# 使用方法
## cobaltstrike不出网服务器上线
* proxy.php上传到目标服务器,确保 [http://www.test.com/proxy.php](http://192.168.1.106:81/proxy.php)可以访问,页面返回 stinger XXX!
* 修改config.ini,示例如下(确保服务器127.0.0.1:8000和127.0.0.1:4444可以正常绑定)
```
[NET-CONFIG]
WEBSHELL = http://www.test.com/proxy.php
SERVER_LISTEN = 127.0.0.1:8000
LOCAL_LISTEN = 127.0.0.1:4444

[TOOL-CONFIG]
LOG_LEVEL = INFO
READ_BUFF_SIZE = 10240
SLEEP_TIME = 0.01
```
* 将mirror_server.exe和config.ini上传到目标服务器同一目录,菜刀(蚁剑)执行mirror_server.exe启动服务端
* 将mirror_client和config.ini上传到CS的teamserver服务器,执行./mirror_client启动客户端,出现如下输出表示成功
```
root@kali:~# ./mirror_client 
2019-08-30 01:42:46,311 - INFO - 220 -  ------------Client Config------------
2019-08-30 01:42:46,311 - INFO - 223 - 
LOG_LEVEL: INFO
SLEEP_TIME:0.01
READ_BUFF_SIZE: 10240
WEBSHELL: http://www.test.com/proxy.php
REMOVE_SERVER: http://127.0.0.1:8000
TARGET_LISTEN: 127.0.0.1:4444
2019-08-30 01:42:46,320 - INFO - 45 -  ------------Server Config------------
2019-08-30 01:42:46,320 - INFO - 49 - 
LOG_LEVEL: INFO
READ_BUFF_SIZE: 10240
SERVER_LISTEN: 127.0.0.1:8000
LOCAL_LISTEN: 127.0.0.1:4444
2019-08-30 01:42:46,320 - INFO - 52 - Connet to server success
```
* cobaltstrike启动监听,host 127.0.0.1 port 4444 beacons 127.0.0.1

![图片](https://uploader.shimo.im/f/uXFSgVE6WFsyksDn.png!thumbnail)
* 使用菜刀(蚁剑)执行在目标机执行该listener的payload,客户端出现如下日志表示正在传输stager,稍后session即可上线
```
2019-08-30 01:47:43,663 - INFO - 52 - Connet to server success
2019-08-30 01:49:46,430 - WARNING - 101 - CLIENT_ADDRESS:127.0.0.1:60487 Create new tcp socket
2019-08-30 01:49:46,538 - INFO - 160 - CLIENT_ADDRESS:127.0.0.1:60487 TCP_SEND_DATA:201
2019-08-30 01:49:46,554 - INFO - 118 - CLIENT_ADDRESS:127.0.0.1:60487 
.................
................
2019-08-30 01:49:46,929 - INFO - 118 - CLIENT_ADDRESS:127.0.0.1:60487 TCP_RECV_LEN:10240

2019-08-30 01:49:49,819 - WARNING - 164 - CLIENT_ADDRESS:127.0.0.1:60487 Client socket closed
2019-08-30 01:49:49,834 - WARNING - 86 - CLIENT_ADDRESS:127.0.0.1:60487 Not in server socket list, remove
2019-08-30 01:49:49,849 - WARNING - 101 - CLIENT_ADDRESS:127.0.0.1:60545 Create new tcp socket
2019-08-30 01:49:49,956 - INFO - 160 - CLIENT_ADDRESS:127.0.0.1:60545 TCP_SEND_DATA:381
2019-08-30 01:49:49,971 - INFO - 118 - CLIENT_ADDRESS:127.0.0.1:60545 TCP_RECV_LEN:116
```
* let`s rock the party

![图片](https://uploader.shimo.im/f/dpQVqNdiyKkH9WNs.png!thumbnail)
## meterpreter_reverse_tcp不出网服务器上线
推荐使用毒刺(stinger)+meterpreter_bind_tcp上线 
# 相关工具
暂时没有公开工具实现此功能
# 已测试
## mirror_server.exe
* windows server 2012
## mirror_client
* kali
## proxy.jsp(x)/php/aspx
* php7.2 
* tomcat7.0 
* iis8.0
# 其他参数
```
[TOOL-CONFIG]
LOG_LEVEL = INFO //日志级别,DEBUG,INFO,WARN,ERROR
READ_BUFF_SIZE = 10240 //TCP读取BUFF(不建议大于10240)
SLEEP_TIME = 0.01 //client每次循环的间隔(秒),该值越大请求webshell次数越少,但传输越也慢
[ADVANCED-CONFIG]
REMOVE_SERVER = http://127.0.0.1:8000 // 用于多级内网穿透(不使用时请勿填写)
TARGET_LISTEN = 192.168.3.100:22// 用于多级内网穿透(不使用时请勿填写)
NO_LOG = True //不打印日志
```

# 更新日志
**1.0**
更新时间: 2019-08-30
* 1.0正式版发布

**1.1**
更新时间: 2019-09-29
* 更新php脚本,速度更快
* 增加jspx脚本适配

