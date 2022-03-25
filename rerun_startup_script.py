'''
    File name: rerun_startup_script.py
    Author: Leonardo Bertini
    Date created: 29/11/2021
    Date last modified: 21/11/2021
    Python Version: 3.7
    Description: This script gets the list of instances of a given project, connects to them through IAP and rerun the startup metatada
'''

from socket import timeout
import subprocess
import json

# Get the list of all the instances in a given project in json format
def get_instance_list(project):
    instance_list = subprocess.Popen(f"gcloud --project={project} compute instances list --format=json", universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output, error = instance_list.communicate()
    parsed_list = json.loads(output)
    instance_list.kill
    return parsed_list

# Log into the instance via IAP and run the command to reload the startup metadata
def rerun_linux_startup_script(project, instance, zone):
    print('\033[1;32m' + instance + '\33[39m')
    iapconnect = f"gcloud --project={project} compute ssh {instance} --tunnel-through-iap --zone={zone} --command='curl https://storage.googleapis.com/rs-gce-instances-scripts-master/linux/startup_scripts/rackspace_gcp_sysprep_v1.sh -o rackspace_gcp_sysprep_v1.sh && chmod u+x rackspace_gcp_sysprep_v1.sh && sudo ./rackspace_gcp_sysprep_v1.sh &'"
    iapcommand = subprocess.Popen(iapconnect, timeout=300, stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('Startup script reload command sent!')
    iapcommand.kill

def main():
    project = input("Enter the project ID:\n")
    instance_list = get_instance_list(project)
    for instance in instance_list:
        # We do not want to rerun the startup scripts on Windows, COS and GKE instances. Suse is also not supported. The OS type is reported in the licence metatada keys
        if ("windows" not in instance["disks"][0]["licenses"][0]) and ("cos-cloud" not in instance["disks"][0]["licenses"][0]) and ("suse-cloud" not in instance["disks"][0]["licenses"][0]) and ("gke" not in instance["name"]):
            rerun_linux_startup_script(project, instance['name'], instance['zone'])  
main()