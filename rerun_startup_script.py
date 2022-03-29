'''
    File name: rerun_startup_script.py
    Author: Leonardo Bertini
    Date created: 29/11/2021
    Date last modified: 21/11/2021
    Python Version: 3.7
    Description: This script gets the list of instances of a given project, connects to them through IAP and rerun the startup metatada
'''

import subprocess
import json
supported_linux = ["ubuntu", "centos", "rhel", "debian"]

# Get the list of all the instances in a given project in json format
def get_instance_list(project):
    instance_list = subprocess.Popen(f"gcloud --project={project} compute instances list --format='json(name,zone,disks)'", universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output, error = instance_list.communicate()
    parsed_list = json.loads(output)
    instance_list.kill
    return parsed_list

# Log into the instance via IAP and run the command to reload the startup metadata
def rerun_linux_startup_script(project, instance, zone):
    print('\033[1;32m' + instance + '\33[39m')
    iapconnect = f"gcloud --project={project} compute ssh {instance} --tunnel-through-iap --zone={zone} --command='curl https://storage.googleapis.com/rs-gce-instances-scripts-master/linux/startup_scripts/rackspace_gcp_sysprep_v1.sh -o rackspace_gcp_sysprep_v1.sh &>/dev/null && chmod u+x rackspace_gcp_sysprep_v1.sh && sudo ./rackspace_gcp_sysprep_v1.sh & &> /dev/null'"
    iapcommand = subprocess.Popen(iapconnect, stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('Startup script reload command sent!')
    iapcommand.kill

def main():
    project = input("Enter the project ID:\n")
    instance_list = get_instance_list(project)
    for instance in instance_list:
        os = None
        exception = None
        for disk in instance['disks']:
            try:
                licenses = disk['licenses']
            except:
                exception = "OS info not found"
            else:
                for license in licenses:
                    if "win" in license:
                        os = "windows"
                        break
                    elif any(item in license for item in supported_linux):
                        os = "linux"
        if os == None and exception != None:
            os = exception
        if os == "linux":
            rerun_linux_startup_script(project, instance['name'], instance['zone'])
        elif os == "windows":
            print('\033[1;32m' + instance['name'] + '\33[39m')
            print('This is a Windows VM')
        else:
            print('\033[1;32m' + instance['name'] + '\33[39m')
            print('OS not supported!\n')
main()