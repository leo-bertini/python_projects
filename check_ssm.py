'''
    File name: check_ssm.py
    Author: Leonardo Bertini
    Date created: 29/11/2021
    Date last modified: 21/11/2021
    Python Version: 3.7
    Description: This script gets the list of instances of a given project and returns which instances are not running the SSM agent
'''

from os import error
import subprocess
import json

# Get the list of all the instances in a given project in json format
def get_instance_list(project):
    instance_list = subprocess.Popen(f"gcloud --project={project} compute instances list --format=json", universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output, error = instance_list.communicate()
    parsed_list = json.loads(output)
    instance_list.kill
    return parsed_list

# Log into the instance via IAP and run the command to check if the SSM agent is running
def check_ssm_linux(project, instance, zone):
    iapconnect = f"""gcloud --project={project} compute ssh {instance} --tunnel-through-iap --zone={zone} --command='sudo systemctl status amazon-ssm-agent --lines=1 | grep "Active:"'"""
    iapsession = subprocess.Popen(iapconnect, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    while iapsession.poll() is None:
        output = iapsession.stdout.readline()
        if "Active:" in output:
            if "inactive (dead)" in output:
                print('\033[1;93m' + instance + '\33[93m' + ": " + "SSM Agent is NOT running, please troubleshoot")
            else:
                print('\033[1;32m' + instance + '\33[39m' + ": " + "SSM agent is running")
        if "service could not be found" in output:
            print('\033[1;93m' + instance + '\33[93m' + ": " + "SSM Agent has not been installed, please troubleshoot")
    iapsession.kill

def main():
    project = input("Enter the project ID:\n")
    instance_list = get_instance_list(project)
    for instance in instance_list:
        # We do not want to rerun the startup scripts on Windows, COS and GKE instances. Suse is also not supported. The OS type is reported in the licence metatada keys
        if "windows" not in instance["disks"][0]["licenses"][0] and "cos-cloud" not in instance["disks"][0]["licenses"][0] and "suse-cloud" not in instance["disks"][0]["licenses"][0] and "gke" not in instance["name"]:
            check_ssm_linux(project, instance['name'], instance['zone'],)

main()