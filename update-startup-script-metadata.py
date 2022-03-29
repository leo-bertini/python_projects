import subprocess
import json

supported_linux = ["ubuntu", "centos", "rhel", "debian"]
linux_startup_script_metadata = 'startup-script-url=https://storage.googleapis.com/rs-gce-instances-scripts-master/linux/startup_scripts/rackspace_gcp_sysprep_v1.sh'
windows_startup_script_metadata = 'sysprep-specialize-script-url=gs://rs-gce-instances-scripts-master/windows/rs-config.ps1'

# Get the list of all the instances in a given project in json format
def get_instance_list(project):
    instance_list = subprocess.Popen(f"gcloud --project={project} compute instances list --format='json(name,zone,disks)'", universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output, error = instance_list.communicate()
    parsed_list = json.loads(output)
    instance_list.kill
    return parsed_list

def add_startup_script(project, instance, zone, startup_script_metadata):
    print('\033[1;32m' + instance + '\33[39m')
    add_metadata = subprocess.Popen(f"gcloud --project={project} compute instances add-metadata {instance} --metadata={startup_script_metadata} --zone={zone}", universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output, error = add_metadata.communicate()
    print (output)
    if (error is not None):
        print (error)
    add_metadata.kill

def main():
    project = input("Enter the project ID:\n")
    instance_list = get_instance_list(project)
    for instance in instance_list:
        os = None
        exception = None
        instance_group = False
        try:
            if ('created-by' in instance['metadata']['items'][0]['key']):
                 instance_group = True
        except:
            None
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
        if (not instance_group) and ('gke' not in instance['name']) :
            if os == 'linux':
                add_startup_script(project, instance['name'], instance['zone'], linux_startup_script_metadata)
            elif os == 'windows':
                add_startup_script(project, instance['name'], instance['zone'], windows_startup_script_metadata)
            else:
                print('\033[1;32m' + instance['name'] + '\33[39m')
                print('OS not supported!\n')
main()