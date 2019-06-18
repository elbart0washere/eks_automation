import os
import json 
import time


def upgrade_eks(eks_name,aws_profile,upgrade_version):
    upgrade = "aws eks --region us-east-1 update-cluster-version --name %s  --kubernetes-version %s --profile %s"%(eks_name,upgrade_version,aws_profile)
    os.system(upgrade) 
    print(upgrade)

def upgrade_status(eks_name,aws_profile,update_id):
    watch = "aws eks --region us-east-1 describe-update --name %s --profile %s --update-id %s --output json"%(eks_name,aws_profile,update_id)
    show_status = os.popen(watch).read()
    data = json.loads(show_status)
    while (data["update"]["status"]) == "InProgress":
        print(data["update"]["status"])
        time.sleep(15)
        show_status = os.popen(watch).read()
        data = json.loads(show_status)

def kube_update(kube_proxy_version):
    kube_proxy_new_version = """kubectl patch daemonset kube-proxy -n kube-system -p '{"spec": {"template": {"spec": {"containers": [{"image": "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/kube-proxy:%s","name":"kube-proxy"}]}}}}'"""%(kube_proxy_version)
    patching = os.popen(kube_proxy_new_version).read()
    print("----Parcheando Kube-proxy----")
    print(patching)

def kube_update_12():
    kube_proxy_new_version = """kubectl patch daemonset kube-proxy -n kube-system -p '{"spec": {"template": {"spec": {"containers": [{"image": "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/kube-proxy:v1.12.6","name":"kube-proxy"}]}}}}'"""
    patching = os.popen(kube_proxy_new_version).read()
    print("----Parcheando Kube-proxy----")
    print(patching)

def coredns_install():
    print("----Preparing coreos env----")
    command = """kubectl patch -n kube-system deployment/kube-dns --patch '{"spec":{"selector":{"matchLabels":{"eks.amazonaws.com/component":"kube-dns"}}}}'"""
    patch_kubectl = os.popen(command).read()
    print(patch_kubectl)
    time.sleep(1)
    print("----Installing coreos----")
    os.system("""curl -o dns.yaml https://amazon-eks.s3-us-west-2.amazonaws.com/cloudformation/2019-02-11/dns.yaml""")
    env_1 = """kubectl get svc -n kube-system kube-dns -o jsonpath='{.spec.clusterIP}'"""
    cluster_ip = os.popen(env_1).read()
    os.environ['DNS_CLUSTER_IP'] = cluster_ip
    env_2 = """us-east-1"""
    os.environ['REGION'] = env_2
    os.system("""cat dns.yaml | sed -e "s/REGION/$REGION/g" | sed -e "s/DNS_CLUSTER_IP/$DNS_CLUSTER_IP/g" | kubectl apply -f -""")
    time.sleep(10)
   
def coredns_upgrade(coreos_version):
    print("----Installing CoreOS version according your K8s version----")
    install_coreos = """kubectl set image --namespace kube-system deployment.apps/coredns coredns=602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/coredns:%s"""%(coreos_version)
    os.popen(install_coreos).read()
    print(install_coreos)

def coredns_upgrade_12(coreos_version):
    print("----Installing CoreOS version according your K8s version----")
    install_coreos = """kubectl set image --namespace kube-system deployment.apps/coredns coredns=602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/coredns:%s"""%(coreos_version)
    os.popen(install_coreos).read()
    print(install_coreos)

def remove_kube_dns():
    downgrade_kube_dns = """kubectl scale -n kube-system deployment/kube-dns --replicas=0"""
    print("----Uninstalling kube-dns----")
    delete_kube_dns = """kubectl delete -n kube-system deployment/kube-dns serviceaccount/kube-dns configmap/kube-dns"""
    os.popen(downgrade_kube_dns).read()
    print(downgrade_kube_dns)
    time.sleep(3)
    os.popen(delete_kube_dns).read()
    print("----kube-dns has been removed----")
    print(delete_kube_dns)

def upgrade_cni():
    upgrade_cni = "kubectl apply -f https://raw.githubusercontent.com/aws/amazon-vpc-cni-k8s/master/config/v1.4/aws-k8s-cni.yaml"
    os.popen(upgrade_cni).read()
    print(upgrade_cni)
    time.sleep(10)

eks_name = input("Insert the EKS cluster name to upgrade: ")
aws_profile = input("Insert your aws profile name : ")
upgrade_version = input("Insert version to upgrade (only support 1.11 & 1.12 values): " )

if upgrade_version == "1.11":
    print("***Starting EKS upgrade to v1.11***")
    upgrade_eks(eks_name,aws_profile,upgrade_version)
    update_id = input("***Insert actualization ID***: ")
    upgrade_status(eks_name,aws_profile,update_id)
    print("***Actualization finished, your control plane it's already running over 1.11 version***")
    time.sleep(2)
    kube_proxy_version = 'v1.11.5'
    print("***Migrating kubeproxy to v1.11.5***")
    kube_update(kube_proxy_version)
    print("***Installing coreDNS***")
    coredns_install()
    print("***Removing kube-dns***")
    remove_kube_dns()
    print("***Setup CoreDNS v1.1.3 for EKS v1.11***")
    coreos_version = 'v1.1.3'
    coredns_upgrade(coreos_version)
    print("***Upgrading CNI to v1.4***")
    upgrade_cni()
    print("***Finishing, now you'll need upgrade the WorkersNodes***")
elif upgrade_version == "1.12":
    print("***Starting EKS upgrade to v1.12***")
    upgrade_eks(eks_name,aws_profile,upgrade_version)
    update_id = input("***Insert actualization ID***: ")
    upgrade_status(eks_name,aws_profile,update_id)
    print("***Actualization finished, your control plane it's currently running over 1.12 version***")
    kube_update_12()
    print("***Installing coreDNS***")
    coredns_install()
    print("***Removing kube-dns***")
    remove_kube_dns()
    print("***Setup CoreDNS v1.2.2 for EKS v1.12***")
    coreos_version = 'v1.2.2'
    coredns_upgrade_12(coreos_version)
    upgrade_cni()
    print("***Finishing, now you'll need upgrade the WorkersNodes***")
else :
    print("""***We don't support upgrade %s ***"""%upgrade_version)

