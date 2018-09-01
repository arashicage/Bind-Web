

<h1 align = "center">Bind-DLZ + Flask  + Mysql  DNS管理平台 </h1>

系统环境:CentOS 7.4 X64

软件版本: 

      bind-9.9.5.tar.gz  
      mysql-5.6.16.tar.gz
描述： 
数据库安装就不在絮叨，了解运维的同学都应该知道

<h2 align = "center">一．源码安装配置Bind: </h2>

1.yum安装<br/>
yum  install  -y bind  mysql-server    mysql<br/>
 

	 
![](https://github.com/1032231418/doc/blob/master/images/1.png?raw=true)



2.配置Bind<br/>
vim /etc/named.conf <br/>

options {<br/>
        listen-on port 53 { 192.168.10.1; };<br/>
        directory       "/etc/named";            #zone文件路径<br/>
        allow-query     { any; };<br/>
        recursion yes;<br/>
        dnssec-enable yes;<br/>

};<br/>

zone  "cdd.group" {<br/>
    type  master;<br/>
    file  "cdd.group.zone";<br/>
            notify yes;<br/>
        allow-transfer { 192.168.10.2; };<br/>
        also-notify { 192.168.10.2; };<br/>
        #allow-update { none; };<br/>
};<br/>


保存退出


3.配置数据库，导入sql 文件

	mysql -p   #登录数据库
	mysql> CREATE DATABASE  named   CHARACTER SET utf8 COLLATE utf8_general_ci; 
	mysql> source named.sql;             #注意路径，这里我放在当前目录
	就两张表，一个dns用到的表，一个用户管理表

![](https://github.com/1032231418/doc/blob/master/images/2.png?raw=true)


监控系统日志：

	 tail -f /var/log/messages
	 
如下，说明服务启动正常

![](https://github.com/1032231418/doc/blob/master/images/3.png?raw=true)

查看启动状态
 tail -f /var/log/messages

![](https://github.com/1032231418/doc/blob/master/images/5.png?raw=true)

<h2 align = "center">二．配置Bind-Web 管理平台 </h2>

上传 Bind-web-1.0.tar.gz 管理平台

	(demo) -bash-4.1# git  clone  https://github.com/guleng/Bind-Web.git  #git  克隆下来
	(demo) -bash-4.1# cd Bind-Web
	(demo) -bash-4.1# python  run.py     

运行软件程序使用flask框架写的，要用pip安装该框架

http://ip/5000   访问WEB 界面 登录账户 eagle 密码 123456

功能有，用户管理，域名管理
#登录页面
![](https://github.com/guleng/Bind-Web/raw/master/image/11.png?raw=true)

#仪表盘
![](https://github.com/guleng/Bind-Web/raw/master/image/22.png?raw=true)

#域名解析页面，有添加删除功能
![](https://github.com/guleng/Bind-Web/raw/master/image/33.png?raw=true)

#添加页面，默认是前端的页面写入cdd.group的定语域名，Bind-Web-master/app/templates/named.html，需要的话更改默认值即可用！
![](https://github.com/guleng/Bind-Web/raw/master/image/44.png?raw=true)

#改程序原理是web段显示的是从数据库里调出来的数据，而bind真正解析的是zone文件里的域名，数据库只是为了<br/>
web显示，每次添加或删除时数据库的和文件里的都删除后reload bind  service，而且<br/>
每次更改时backup目录里做一次备份更改之前的备份，保证丢失记录<br/>

<br/>
<br/>
<br/>
<br/>



BUG修改记录<br/>
更改原只支持数据库模式加支持文本配置模式<br/>
增加输入框的默认值<br/>
增加判断输入框的值是否有效功能<br/>
修复原添加不成功无报错bug加提示<br/>
修复二级域名的重复添加bug<br/>
增加id的增长与服务的reload方法<br/>
增加配置文件的备份函数<br/>
文字的修改与图片的更改<br/>
把添加域名的函数和添加用户的函数分开，原是同一个来着<br/>
增加数据库连接端口好指定配置<br/>
修复10行以上无法删除与修改bug<br/>
增加更新域名时重复和ip地址的有效性判断<br/>
