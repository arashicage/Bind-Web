#!/bin/bash
nohup python /etc/named/Bind-Web-master/run.py >> /etc/named/Bind-Web-master/bind-system.log   2>&1  &
