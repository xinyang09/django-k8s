from django.shortcuts import render
from django.http import JsonResponse, QueryDict
from .forms import UploadFileForm
import paramiko
from devops import k8s_tools  # 导入k8s登陆封装
from kubernetes import client, config
import os
def handle_uploaded_file(f, sftp_path):
    # 使用paramiko连接到SFTP服务器
    transport = paramiko.Transport(('sftp.yourserver.com', 22))
    transport.connect(username='yourusername', password='yourpassword')
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.putfo(f, sftp_path)
    sftp.close()
    transport.close()

@k8s_tools.self_login_required
def list(request):
    return render(request, "files/files.html")

@k8s_tools.self_login_required
def files_api(request):
    hostname = 'collearn.cn'
    port = 30022
    username = 'sftp'
    password = 'Xinyang666!'
    remote_path = 'upload'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)
    sftp = ssh.open_sftp()
    files = sftp.listdir(remote_path)
    sftp.close()
    ssh.close()
    print(files)
    data = {"name":"1.py",}
    code = 0
    msg = "获取成功"
    count = len(data)
    res = {'code': code, 'msg': msg, 'count': count, 'data': data}

    print(res)
    return JsonResponse(res)


def preview_file(request):
    if request.method == "GET":
        file_name = request.GET.get("name")
        sftp_host = "collearn.cn"
        sftp_port = 30022
        sftp_username = "sftp"
        sftp_password = "Xinyang666!"
        sftp_directory = "upload"


        try:
            transport = paramiko.Transport((sftp_host, sftp_port))
            transport.connect(username=sftp_username, password=sftp_password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            file_path = sftp_directory + file_name
            with sftp.open(file_path, 'r') as file:
                content = file.read()

            sftp.close()
            transport.close()
            return JsonResponse({"code": 200, "content": content.decode('utf-8'), "msg": "获取成功"})
        except Exception as e:
            return JsonResponse({"code": 1, "msg": str(e)})


def export_resource_api(request):
    code = "1"
    msg = "未知错误"
    result = ""  # 初始化result
    try:
        namespace = request.GET.get('namespace', None)
        resource = request.GET.get('resource', None)
        name = request.GET.get('name', None)

        # 你的业务逻辑，处理 namespace、resource 和 name
        # 例如，从Kubernetes中获取相应资源并赋值给 result

        code = "200"
        msg = "获取成功"
    except Exception as e:
        msg = str(e)

    res = {"code": code, "msg": msg, "data": result}
    return JsonResponse(res)


def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'], '/path/on/sftp/server/' + request.FILES['file'].name)
            return JsonResponse({'code': 0, 'msg': '上传成功'})
        else:
            return JsonResponse({'code': 1, 'msg': '表单无效'})
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})
