'''
    File name: deploy_o+_alerts.py
    Author: Leonardo Bertini
    Date created: 04/08/2023
    Date last modified: 08/08/2023
    Python Version: 3.7
    Description: This script authenticates the user on a O+ customer project via janus and deploys monitoring alerts from repo https://github.com/rackspace-infrastructure-automation/mgcp-terraform-modules.git.
    Inputs: sso username, sso password, project ID, primary email address (for alert notification), deploy NAT alert yes|no, deploy CSQL alert yes|no.
'''

import os, shutil, subprocess, requests, json
from getpass import getpass


dir = "o+_alerts_repo"
path = os.path.join(os.path.expanduser("~"), "Documents", dir)

# Checks if gcloud is configured to use janus account and if Application Default credential file is present
def verify_gloud_config():
    account = json.loads(subprocess.check_output("gcloud config list --format=json", shell=True, universal_newlines=True))["core"]["account"]
    credential_file_exists = os.path.exists(os.path.join(os.path.expanduser("~"), ".config/gcloud/application_default_credentials.json"))
    if account.startswith("racker") and account.endswith("@gcp.rackspace.com") and credential_file_exists:
        return True
    elif not account.startswith("racker") or not account.endswith("@gcp.rackspace.com"):
        print("\033[0;91mThe account selected in gcloud is not your janus account, process aborted!\033[0;m")
        exit()
    elif not credential_file_exists:
        print("\033[0;91mNo application credential file found!\033[0;m")
        print("Please run: '\033[0;32mgcloud auth application-default login\033[0;m' under your janus account then rerun the script.")
        exit()
             
# Clones github repo locally
def clone_repo():
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
        os.mkdir(path)
    else:
        os.mkdir(path)

    clone_repo = subprocess.run(f"git -C {path} clone https://github.com/rackspace-infrastructure-automation/mgcp-terraform-modules.git", universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    print (clone_repo)

def request_webhook_secret (token, project_id, ddi):
    url = f"https://watchman.api.manage.rackspace.com/v0/gcpProjects/{project_id}/webhooks"
    headers = {'X-Auth-Token': token, 'x-tenant-id': ddi, 'Content-Type': 'application/json'}
    secret = json.loads(requests.get(url, headers=headers).text)['webhooks'][0]['href']
    return secret[secret.index("secret=") +7 : secret.index("&severity=")]


# Requests token for janus auth
def request_token(sso, password):
     url = 'https://identity-internal.api.rackspacecloud.com/v2.0/tokens'
     data = '{"auth": {"RAX-AUTH:domain": {"name": "Rackspace"},"passwordCredentials": {"username": "'+sso+'","password": "'+password+'"}'+'}'+'}'
     headers = 'Content-Type: application/json'
     response = json.loads((requests.post(url, data, headers)).text)
     return response['access']['token']['id']

# Requests permissions on the given project
def janus_auth(token, project_id):
     url = 'https://gcp.api.manage.rackspace.com/v1alpha/accessGrants'
     data = '{ "projectId": "'+project_id+'"}'
     headers = {'X-Auth-Token': token, 'Content-Type': 'application/json', 'accept': 'application/json'}
     json.loads((requests.post(url, data, headers=headers)).text)
     janus_response_code = requests.post(url, data, headers=headers)
     if "201" in janus_response_code:
          return True
     else:
        return janus_response_code

def url_index_conversion(index):
    if index == 1:
        return "first"
    elif index == 2:
        return "second"
    elif index == 3:
        return "third"

# Request the required user inputs
def request_input():
    global project_id, ddi, sso, password, urls
    sso = input("Please type your SSO: ")
    password = getpass(prompt="Please type your SSO password: ", stream=None)
    project_id = input("Please type the project ID where the alert policies will be deployed: ")
    ddi = input("Please type the Customer DDI: ")
    while(True):
        url_check_number = int(input("How many URL checks the customer would like to have configured? (Max 3 URL checks): "))
        if url_check_number in range (0,4):
            break
        else:
            print(f"\033[0;91mPlease enter a valid number!\033[0;m")

    counter = 0
    urls = []
    if url_check_number > 0:
        while (counter < url_check_number):
            url = input(f"Please type the {url_index_conversion(counter + 1)} URL (Example: https://www.rackspace.com): ")
            if all(not url.startswith(items) for items in ["http://", "https://"]):
                print("\033[0;91mThe URL is not in the corret format, please make sure type 'http://' or 'https://' at the beginning of the URL.\033[0;m")
            else:
                urls.append(url)
                counter = counter +1
        urls = json.dumps(urls)
    else:
        urls = "[]"
    print()
    print()
    print("These are the chosen values:")
    print()
    print(f"SSO = \033[0;32m{sso}\033[0;m")
    print(f"Password = \033[0;32m******\033[0;m")
    print(f"Project ID = \033[0;32m{project_id}\033[0;m")
    print(f"DDI = \033[0;32m{ddi}\033[0;m")
    print(f"URLs to monitor = \033[0;32m{urls}\033[0;m")
    print()

# Deploys the O+ monitors via terraform
def terraform_deploy(secret):
        subprocess.run("terraform init", stdout=subprocess.PIPE, shell=True)
        output = json.loads('['+subprocess.check_output(f"terraform apply -json -var project_id={project_id} -var watchman_token={secret} -var 'url_list={urls}' -auto-approve", shell=True, universal_newlines=True).replace('\n', ',')[:-1]+']')
        return json.dumps(output[-2]["@message"], indent=1)

# Cleans up the local repo and script file
def clean_up():
    shutil.rmtree(path, ignore_errors=True)
    os.remove(f"{os.path.dirname(__file__)}/{os.path.basename(__file__)}")


# Main function
def main():
    verify_gloud_config()
    clone_repo()

    accept_input = "no"

    while (accept_input != "yes"): # Loops until inputs are confirmed
        request_input()
        accept_input = input("Are all the values correct? Please type yes|no: ")
        print()
    
    if accept_input == "yes":
         print(f"Deploying alert policies on project \033[0;32m{project_id}\033[0;m...")
         print()

    os.chdir(f"{path}/mgcp-terraform-modules/optimizer-plus-standard-alerts")

    token = request_token(sso, password)
    secret = request_webhook_secret(token, project_id, ddi)

    janus_auth_response = janus_auth(token, project_id)
    if janus_auth_response:
        print(f"\033[0;32m{terraform_deploy(secret)}\033[0;m")
    else:
        print(f"\033[0;91mJanus failed to grant access to the project. Process aborted! Error: {janus_auth_response}\033[0;m")    
    clean_up()

main()
