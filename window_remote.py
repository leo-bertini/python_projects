#import winrm
from os import error
import subprocess
import json

def get_instance_list(project):
    instance_list = subprocess.Popen(f"gcloud --project={project} compute instances list --format=json", universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output, error = instance_list.communicate()
    parsed_list = json.loads(output)
    instance_list.kill
    return parsed_list

def get_windows_password(project, instance, zone):
    session = subprocess.Popen(f"gcloud --project={project} compute reset-windows-password {instance} --zone={zone} --format=json --quiet", universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = session.communicate()
    parsed_ouput = json.loads(output)
    return parsed_ouput['password']

def check_ssm_windows(project, instance, zone):
    iap_command = f"gcloud --project={project} compute start-iap-tunnel {instance} 5985 --local-host-port=localhost:5985 --zone={zone}"
    iap_tunnel = subprocess.Popen(iap_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

def main():
    project = input("Enter the project ID:\n")
    instance_list = get_instance_list(project)
    for instance in instance_list:
        # We do not want to rerun the startup scripts on Windows, COS and GKE instances. Suse is also not supported. The OS type is reported in the licence metatada keys
        if "windows" in instance["disks"][0]["licenses"][0]:
            password = get_windows_password(project, instance['name'], instance['zone'])

main()
