#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
# Author:shichao
# File: .py


from kubernetes import client,config
import os,hashlib,random
from django.shortcuts import redirect # 重定向

def auth_check(auth_type,str):
    print(auth_type)
    if auth_type == "password":
        token = str
        configuration = client.Configuration()
        configuration.host = "https://api.collearn.cn:6443"  # APISERVER地址
        configuration.ssl_ca_cert = os.path.join("kubeconfig", "ca.crt") # CA证书
        configuration.verify_ssl = True  # 启用证书验证
        configuration.api_key = {"authorization": "Bearer " + token}  # 指定Token字符串
        client.Configuration.set_default(configuration)
        try:
            core_api = client.CoreApi()  # namespace,pod,service,pv,pvc
            core_api.get_api_versions()  # 查询资源测试
            return True
        except Exception as e:
            print(e)
            return False

    elif auth_type == "kubeconfig":
        random_str = str
        file_path = os.path.join("kubeconfig",random_str)
        config.load_kube_config(r"%s" % file_path)
        try:
            core_api = client.CoreApi()  # namespace,pod,service,pv,pvc
            core_api.get_api_versions()  # 查询资源测试
            return True
        except Exception as e:
            print(e)
            return False



# 登陆装饰器，判断session是否存在，不存在跳转到登陆页面
def self_login_required(func):
    def inner(request,*args,**kwargs):
        is_login = request.session.get("is_login",False)
        if is_login:
            return func(request,*args,**kwargs)
        else:
            return redirect("/login")
    return inner


# 加载认证配置
def load_auth_config(auth_type,str):
    if auth_type == "password":
        token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IkdIREFLZEd2S2puMU1lSF9mQWVheG0zUGNmbXFIbjVpQ3NJR0tOeWdSMVEifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJuYW1lc3BhY2UtY29udHJvbGxlci10b2tlbi1oY3FqdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJuYW1lc3BhY2UtY29udHJvbGxlciIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImUyYzI5ZGRkLTI3NTItNGY2My05OGZhLWVlNzAyNzg0MDVlOCIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlLXN5c3RlbTpuYW1lc3BhY2UtY29udHJvbGxlciJ9.U5574Zvnn05382Xh6S8AruJnWiyVhI79M_jtbq1F_2-tyKIAgyZjvmYaAe-6mAIOBbiGmF7nQ1cFohnXpZoswX9COEgVvZG0qw5wz8oY6TgeRUAwZjf64zmGAirOyd2Y5l_Lp_Du2OMV7Y46gpwg65cOL9tqHnQkMrOs3YztKPiFrMcjJgV8UGhqR79fNqGbby8I7XJwNf-YgT6jOInm-Bi26WUGNvlEZJI2BlArbOxiEvK0p6zhh7DYaKkizRXaTX1iBLbCKFM1c-PN03dhZustttCDPMvXr085BH9jmgCSnholG4jIuW-joTo-IAg2lYOAGTMbzj3ya_SuY5XS7Q'
        configuration = client.Configuration()
        configuration.host = "https://collearn.cn:6443"  # APISERVER地址
        configuration.ssl_ca_cert = r"%s" %(os.path.join('kubeconfig', "ca.crt")) # CA证书
        configuration.verify_ssl = True  # 启用证书验证
        configuration.api_key = {"authorization": "Bearer " + token}  # 指定Token字符串
        client.Configuration.set_default(configuration)
    elif auth_type == "kubeconfig":
        random_str = str
        file_path = os.path.join("kubeconfig",random_str)
        config.load_kube_config(r"%s" % file_path)



# 时间格式化
from datetime import  date,timedelta
def dt_format(timestamp):
    t = date.strftime((timestamp + timedelta(hours=8)),'%Y-%m-%d %H:%M:%S')
    return  t