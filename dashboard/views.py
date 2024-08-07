from django.shortcuts import render,redirect
from django.http import HttpResponse, HttpRequest, JsonResponse, QueryDict
from kubernetes import client, config
import os, random, hashlib  # 导入工具
from devops import k8s_tools  # 导入k8s登陆封装
from django.shortcuts import redirect  # 重定向
from dashboard import node_data  # 导入计算模块
from django.http import HttpResponse
from .forms import IngressForm



# Create your views here.
@k8s_tools.self_login_required
def index(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s_tools.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    # echart图表：通过ajax动态渲染/dashboard/node_resource接口获取
    # 工作负载：访问每个资源的接口，获取count值ajax动态渲染

    # 节点状态
    n_r = node_data.node_resource(core_api)

    # 存储资源
    pv_list = []
    for pv in core_api.list_persistent_volume().items:
        pv_name = pv.metadata.name
        capacity = pv.spec.capacity["storage"]  # 返回字典对象
        access_modes = pv.spec.access_modes
        reclaim_policy = pv.spec.persistent_volume_reclaim_policy
        status = pv.status.phase
        if pv.spec.claim_ref is not None:
            pvc_ns = pv.spec.claim_ref.namespace
            pvc_name = pv.spec.claim_ref.name
            claim = "%s/%s" % (pvc_ns, pvc_name)
        else:
            claim = "未关联PVC"
        storage_class = pv.spec.storage_class_name
        create_time = k8s_tools.dt_format(pv.metadata.creation_timestamp)

        data = {"pv_name": pv_name, "capacity": capacity, "access_modes": access_modes,
                "reclaim_policy": reclaim_policy, "status": status,
                "claim": claim, "storage_class": storage_class, "create_time": create_time}
        pv_list.append(data)

    return render(request, 'index.html', {"node_resouces": n_r, "pv_list": pv_list})


from django.shortcuts import render, redirect
from django.http import JsonResponse

def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    elif request.method == "POST":
        user = request.POST.get("username", None)
        pwd = request.POST.get("password", None)
        if user == "admin" and pwd == "admin":
            # 添加session会话
            request.session['is_login'] = True
            request.session['auth_type'] = 'password'
            request.session['user'] = user
            code = "200"
            msg = "认证成功"
        else:
            code = "1"
            msg = "用户名或密码错误"

        res = {"code": code, "msg": msg}
        return JsonResponse(res)



def logout(request):
    request.session.flush()
    return redirect("login")  # 跳转到登录页面


# 仪表盘计算资源，为了方便ajax GET准备的接口
@k8s_tools.self_login_required
def node_resource(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s_tools.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    res = node_data.node_resource(core_api)
    return JsonResponse(res)


# 命名空间接口
@k8s_tools.self_login_required
def namespace_api(request):
    code = 0
    msg = "执行数据返回成功"
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s_tools.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()
    # 命名空间选择和命名空间表格同时使用
    if request.method == "GET":

        # 获取搜索分页的传回来的值
        search_key = request.GET.get("search_key")

        # 空列表
        data = []
        try:
            for i in core_api.list_namespace().items:
                name = i.metadata.name
                labels = i.metadata.labels
                create_time = k8s_tools.dt_format(i.metadata.creation_timestamp)  # 使用函数规则，优化时间返回格式
                namespace = {"name": name, 'labels': labels, 'create_time': create_time}

                # 根据前端返回的搜索key进行判断，查询关键字返回数据
                search_key = request.GET.get('searchkey', None)
                if search_key:
                    if search_key == name:
                        data.append(namespace)
                    elif search_key in name:
                        data.append(namespace)
                else:
                    data.append(namespace)

                code = 0
                msg = "执行数据返回成功"
        except Exception as e:
            code = 1
            # 获取返回状态吗，进行数据判断
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限"
            else:
                msg = "获取数据失败"

        # 统计有多少行数据
        count = len(data)

        # 这里判断是因为，命名选择调用没有分页参数，需要做if分页判断
        if request.GET.get('page'):
            # 分页
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit'))
            # 从哪里开始切
            start = (page - 1) * limit
            # 结束
            end = page * limit

            # 重新封装数据
            data = data[start:end]

        res = {"code": code, "msg": msg, "count": count, "data": data}
        return JsonResponse(res)

    # 创建命名空间
    elif request.method == "POST":
        # 方法是一样的，
        #   print(request.POST["name"])就算没有值也不会报错,返回none，
        #   print(request.POST.get("name", None))取不到值就会报错，
        # print(request.POST.get("name", None))
        # print(request.POST["name"])
        name = request.POST["name"]

        # 判断命名空间是否存在
        for i in core_api.list_namespace().items:
            if name == i.metadata.name:
                res = {'code': 1, "msg": "命名空间已经存在！"}
                return JsonResponse(res)

        try:
            # 创建k8s的模板
            body = client.V1Namespace(
                api_version="v1",
                kind="Namespace",
                metadata=client.V1ObjectMeta(
                    name=name
                )
            )
            core_api.create_namespace(body=body)
            code = 0
            msg = "创建成功"
        except Exception as e:
            code = 1
            # 获取返回状态吗，进行数据判断
            status = getattr(e, "status")
            if status == 403:
                msg = "没有创建权限"
            else:
                msg = "创建失败"
        res = {"code": code, "msg": msg}
        return JsonResponse(res)


    # namespace删除命名空间
    elif request.method == "DELETE":
        # 通过QueryDict 获取ajax提交提交的删除data返回参数
        request_data = QueryDict(request.body)

        # 通过变量获取name参数
        name = request_data.get("name")

        # 认证系统
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s_tools.load_auth_config(auth_type, token)
        core_api = client.CoreV1Api()

        try:
            core_api.delete_namespace(name)  # 删除namespace
            code = 0
            msg = "删除成功"
        except Exception as e:
            code = 1
            # 获取返回状态吗，进行数据判断
            status = getattr(e, "status")
            if status == 403:
                msg = "没有删除权限"
            else:
                msg = "删除失败"
        res = {"code": code, "msg": msg}
        return JsonResponse(res)


# 编写yaml获取数据接口
@k8s_tools.self_login_required
def export_resource_api(request):
    auth_type = request.session.get("auth_type")
    print(auth_type)
    token = request.session.get("token")
    k8s_tools.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()  # namespace, pod ,service,pv,pvc
    apps_api = client.AppsV1Api()  # deployment
    networking_api = client.NetworkingV1Api()  # ingress
    storage_api = client.StorageV1Api  # storage_class

    namespace = request.GET.get("namespace", None)
    resource = request.GET.get("resource", None)
    name = request.GET.get("name", None)
    import yaml, json  # 导入yaml模块使用

    # 获取deployment点击yaml数据
    if resource == "namespaces":
        try:
            # 坑，不要写py测试，print会二次处理影响结果，到时测试不通
            result = core_api.read_namespace(name=name, _preload_content=False).read()
            result = str(result, "utf-8")  # bytes转字符串
            result = yaml.safe_dump(json.loads(result))  # str/dict -> json -> yaml
        except Exception as e:
            code = 1
            msg = e
    elif resource == "deployments":
        try:
            result = apps_api.read_namespaced_deployment(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "replicaset":
        try:
            result = apps_api.read_namespaced_replica_set(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "daemonsets":
        try:
            result = apps_api.read_namespaced_daemon_set(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "statefulsets":
        try:
            result = apps_api.read_namespaced_stateful_set(name=name, namespace=namespace,
                                                           _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "pods":
        try:
            result = core_api.read_namespaced_pod(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "services":
        try:
            result = core_api.read_namespaced_service(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "ingresses":
        try:
            result = networking_api.read_namespaced_ingress(name=name, namespace=namespace,
                                                            _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "pvc":
        try:
            result = core_api.read_namespaced_persistent_volume_claim(name=name, namespace=namespace,
                                                                      _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "PersistentVolumes":
        try:
            result = core_api.read_persistent_volume(name=name, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "nodes":
        try:
            result = core_api.read_node(name=name, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "configmaps":
        try:
            result = core_api.read_namespaced_config_map(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "secrets":
        try:
            result = core_api.read_namespaced_secret(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "secrets":
        try:
            result = core_api.read_namespaced_secret(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    code = 0
    msg = "数据获取成功"
    res = {"code": code, "msg": msg, "data": result}
    return JsonResponse(res)


# 返回yaml页面


def create_ingress(request):
    if request.method == 'POST':
        form = IngressForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            namespace = form.cleaned_data['namespace']
            host = form.cleaned_data['host']
            path = form.cleaned_data['path']
            service_name = form.cleaned_data['service_name']
            service_port = form.cleaned_data['service_port']

            config.load_kube_config()
            api_instance = client.NetworkingV1Api()
            ingress = client.V1Ingress(
                metadata=client.V1ObjectMeta(name=name),
                spec=client.V1IngressSpec(
                    rules=[client.V1IngressRule(
                        host=host,
                        http=client.V1HTTPIngressRuleValue(
                            paths=[client.V1HTTPIngressPath(
                                path=path,
                                backend=client.V1IngressBackend(
                                    service=client.V1IngressServiceBackend(
                                        name=service_name,
                                        port=client.V1ServiceBackendPort(
                                            number=service_port
                                        )
                                    )
                                )
                            )]
                        )
                    )]
                )
            )
            api_instance.create_namespaced_ingress(namespace=namespace, body=ingress)
            return HttpResponse('Ingress created successfully')
    else:
        form = IngressForm()
    return render(request, 'create_ingress.html', {'form': form})


# 允许跨站访问
from django.views.decorators.clickjacking import xframe_options_exempt


@xframe_options_exempt
def ace_editor(request):
    d = {}
    namespace = request.GET.get("namespace", None)
    resource = request.GET.get("resource", None)
    name = request.GET.get("name", None)
    d['namespace'] = namespace
    d['resource'] = resource
    d['name'] = name
    return render(request, "ace_editor.html", {'data': d})
