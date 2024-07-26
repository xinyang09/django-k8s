from django import forms
# 表单类
class IngressForm(forms.Form):
    name = forms.CharField(label='Ingress Name', max_length=100)
    namespace = forms.CharField(label='Namespace', max_length=100)
    host = forms.CharField(label='Host', max_length=100)
    path = forms.CharField(label='Path', max_length=100)
    service_name = forms.CharField(label='Service Name', max_length=100)
    service_port = forms.IntegerField(label='Service Port')


