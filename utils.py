#!/usr/bin/env  python
#_*_ coding:utf-8 _*_
__author__ = 'Eagle'
import MySQLdb as mysql
import config
import commands
import os
import re
import shutil
import time

connect_db = mysql.connect(
                           user   =  config.db_user,
                           passwd =  config.db_passwd,
                           db     =  config.db_name ,
                           host   =  config.db_host,
                           port   =  config.db_port,
                           charset=  "utf8" )
cur = connect_db.cursor()

#每次更新id加1&reload服务
def reload_service():
    bak_time = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
    #域名文件的备份
    if os.path.exists('/etc/named/Bind-Web-master/backup'):
        shutil.copyfile("cdd.group.zone", "backup/cdd.group.zone_%s" % bak_time)
    else:
        os.mkdir('backup')
        shutil.copyfile("cdd.group.zone", "backup/cdd.group.zone_%s" % bak_time)
    
    (status, output) = commands.getstatusoutput('grep serial cdd.group.zone')
    s , b  = output.split(';')
    pre_value = int(s)+1
    value = "                    " + str(pre_value) +  ";    "  + "serial"
    os.system("sed -i '3s/.*serial/%s/g' cdd.group.zone" % value)
    os.system("systemctl reload named.service")

# 获得注册信息，并写入数据库
def insert_sql(table_name,field,data):
    sql = "INSERT INTO %s (%s) VALUES (%s);" % (table_name, ','.join(field), ','.join(['"%s"' % data[x] for x in field]))
    print sql
    ip =  str(data['data'])
    zone = data['zone']
    host = data['host']
    typees = data['type'] 
    #从库查看要添加的二级域名
    check_host = 'select host  from dns_records  where host="%s";' % host 
    cur.execute(check_host)
    select_host = cur.fetchone() 
    #要是存在直接报错
    if select_host:
        res = int(0)
    else:
        #不存在就添加
        res = cur.execute(sql)
        connect_db.commit()
        with open('cdd.group.zone','a+') as f:
            f.write("%s    %s     %s\n" % (host,typees,ip))
        #写入成功更改id和reload服务
        reload_service()
        res = int(1) 
    if  res:
        result = {'code':0,'msg':'insert ok'}
    else:
        result = {'code':1,'msg':'insert fail'}
    return result

# 获得数据列表  
def list(table_name,field):
    sql = "select  *  from %s ;" % table_name
    cur.execute(sql)
    res = cur.fetchall()
    if res:
        user = [dict((k,row[i]) for i,k in enumerate(field))for row in res]
        result = {'code':0,'msg':user}
    else:
        result = {'code':1,'errmsg':'data is null'}

    return  result
# 获取一条数据
def getone(table,data,field):
    if data.has_key('username'):
        sql = 'select * from %s where username="%s";' % (table,data['username'])
    else:
        sql = 'select %s  from %s where id="%s";' % (','.join(field),table,data['id'])
    print sql
    cur.execute(sql)
    res = cur.fetchone()
    if res:
        user = {k:res[i] for i,k in enumerate(field)}
        result  = {'code':0,'msg':user}
    else:
        result ={'code':1, 'msg':"data is null"}
    return result 

# 数据更新
def _update(table,field,data): 
    conditions = ["%s='%s'" % (k,data[k]) for k in data]
    sql = "update %s set %s where id=%s ;" %(table,','.join(conditions),data['id'])
    check_hosts  = 'select host  from dns_records  where id="%s";' % data['id']
    cur.execute(check_hosts)
    old_host = str(cur.fetchone()).split("'")[1]

    ip = str(data['data'])
    zone = data['zone']
    host = data['host']
    typees = data['type']
    print sql 
    #从库查看该二级域名
    check_host = 'select host  from dns_records  where host="%s";' % host
    cur.execute(check_host)
    select_host = cur.fetchone()

    #判断更新的ip地址是否合法,合法跳过这if,不合法测直接return error
    if not re.match('^(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[1-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[1-9])$','%s' % ip):
        result = {'code':2,'errmsg':'check ip fail'}
        return result

    #要是存在并且这次的域名和原有的域名同样就认为改ip
    if host == old_host:
        os.system("sed -i 's/^%s [ \t].*/%s         %s          %s /g' cdd.group.zone" % (old_host,host,typees,ip))
        res = cur.execute(sql)
    elif select_host:
       #这次的域名和原有的域名不同并且更新的域名存在就报错
        res = int(0)
    else:
       #要是原域名和这次的不同并且库里不存在就变更原记录
        os.system("sed -i 's/^%s [ \t].*/%s         %s         %s /g' cdd.group.zone" % (old_host,host,typees,ip))
        res = cur.execute(sql)
    if res :
        #成功更改完服务reload操作
        reload_service()
        connect_db.commit()
        result = {'code':0,'msg':'update ok'}
    else:
        result = {'code':1,'errmsg':'Update fail'}
    return result 


# 数据删除
def _delete(table_name,data):
    tag=False

    check_hosts  = 'select host  from dns_records  where id="%s";' % data['id']
    cur.execute(check_hosts)
    host = str(cur.fetchone()).split("'")[1]
    print host
    try:
        #直接配置文件里删除后reload
        os.system("sed -i '/^%s [ \t].*/d' cdd.group.zone" % host)
        reload_service()
        #从库表里删除记录值
        sql = 'DELETE FROM %s where id="%s" ;' % (table_name,data['id'])
        if  cur.execute(sql):
            connect_db.commit()
            tag=True
    except Exception, e:
        print 'Error %s' % (sql)
    return   tag

# 用户是否存在监测
def check(table,field,where):
    if isinstance(where, dict) and where:
        conditions = []
        for k,v in where.items():
            conditions.append("%s='%s'" % (k, v))
    sql = "select %s from %s where %s ;" % (','.join(field),table,' AND '.join(conditions))
    print sql
    try:
        if  cur.execute(sql):
            res = cur.fetchone()
            print res
            user =  {k:res[i] for i,k in enumerate(field)}
            print user
            result  = {'code':0,'msg':user}
        else:
            result ={'code':1, 'msg':"data is null"}
    except Exception, e:
        result ={'code':1, 'msg':"SQL Error "}

    return  result

# 用户数据更新
def _updates(table,field,data):
    conditions = ["%s='%s'" % (k,data[k]) for k in data]
    sql = "update %s set %s where id=%s ;" %(table,','.join(conditions),data['id'])
    print sql
    res = cur.execute(sql)
    if res :
        connect_db.commit()
        result = {'code':0,'msg':'update ok'}
    else:
        result = {'code':1,'errmsg':'Update fail'}
    return result


# 用户数据删除
def _deletes(table_name,data):
    tag=False
    try:
        sql = 'DELETE FROM %s where id="%s" ;' % (table_name,data['id'])
        if  cur.execute(sql):
            connect_db.commit()
            tag=True
    except Exception, e:
        print 'Error %s' % (sql)
    return   tag

# 获得用户注册信息，并写入数据库
def insert_sqls(table_name,field,data):
    sql = "INSERT INTO %s (%s) VALUES (%s);" % (table_name, ','.join(field), ','.join(['"%s"' % data[x] for x in field]))
    print sql
    res = cur.execute(sql)
    connect_db.commit()
    if  res:
        result = {'code':0,'msg':'insert ok'}
    else:
        result = {'code':1,'msg':'insert fail'}
    return result
