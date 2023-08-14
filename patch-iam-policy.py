import subprocess, json, os

project = os.getenv('WIP_PROJECT_ID')

def get_project_iam():
    # Collect existing IAM policies
    get_policy = subprocess.run(f"gcloud projects get-iam-policy {project} --format=json",universal_newlines=True, stdout=subprocess.PIPE, shell=True)
    output = get_policy.stdout
    return output

def update_project_iam(iam_policy):
    # Overwrite all the policies with the new policy file
    with open('/tmp/patch_iam_policy.json', 'w') as file:
        json.dump(iam_policy, file)
    set_policy = subprocess.run(f"gcloud projects set-iam-policy {project} /tmp/patch_iam_policy.json --quiet",universal_newlines=True, stdout=subprocess.PIPE, shell=True)
    os.remove("/tmp/patch_iam_policy.json")

def main():
    # project = input("Enter the project ID:\n")
    get_iam = json.loads(get_project_iam())

    # Dump existing policies into a file for backup
    with open(f'/tmp/{project}_iam_policy_bak.json', 'w') as file:
        json.dump(get_iam, file)

    # Checks if sts.gogoleapis.com audit log is already enabled
    if "auditConfigs" in get_iam :
        for auditLogConfig in get_iam["auditConfigs"]:
            try:
                if "sts.googleapis.com" in auditLogConfig["service"]:
                    audit_group_exists = True
                    break
                else:
                    audit_group_exists = False
            except:
                None
    else:
        audit_group_exists = False
    # Remove etag to allow policy update 
    get_iam.pop("etag")

    # If no audit logs have been configured, it creates a new element for Audit logs
    if "auditConfigs" not in get_iam:
        get_iam.update({"auditConfigs": [{"auditLogConfigs": [{"logType": "ADMIN_READ"}, {"logType": "DATA_READ"}, {"logType": "DATA_WRITE"}], "service": "sts.googleapis.com"}]})
        update_project_iam(get_iam)
        print(get_project_iam())

    # If there are already other Audit Logs configured, it just adds the new one to the existing config
    elif "auditConfigs" in get_iam and not audit_group_exists:
       get_iam["auditConfigs"].append({"auditLogConfigs": [{"logType": "ADMIN_READ"}, {"logType": "DATA_READ"}, {"logType": "DATA_WRITE"}], "service": "sts.googleapis.com"})
       update_project_iam(get_iam)
       print(get_project_iam())

    else:
        print("Nothing to update")

main()