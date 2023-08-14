import subprocess, csv, json
from datetime import date
csv_file_path = f"/tmp/org_iam_policy-{date.today()}.csv"

def get_project_iam(project):
    # Collect existing IAM policies
    get_policy = subprocess.run(f"gcloud projects get-iam-policy {project} --format=json",universal_newlines=True, stdout=subprocess.PIPE, shell=True)
    output = get_policy.stdout
    return output

def get_org_project():
    # Collect list of projects
    project_list = subprocess.run("gcloud projects list --format=json",universal_newlines=True, stdout=subprocess.PIPE, shell=True)
    output = project_list.stdout
    return output

def convert_to_csv(json_iam,project):
    # Append iam policies to the same csv file
    with open(csv_file_path,'a', newline='') as csv_file:
        converter=csv.writer(csv_file, delimiter=',')
        for members in json_iam["bindings"]:
            for member in members["members"]:
                converter.writerow([member, members["role"], project])

def main():
    with open(csv_file_path,'w') as csv_file:
        headers = ['Member','Role', 'Project']
        add_headers = csv.DictWriter(csv_file, fieldnames=headers)
        add_headers.writeheader() # Initilize csv file and add headers 

    projects = json.loads(get_org_project()) # Gather Lists all active projects, where the active account has Owner, Editor, Browser or Viewer permissions

    print("Generating csv file...")

    for project in projects: # loop through the list of projects and generates a consolidated csv file
        get_iam = json.loads(get_project_iam(project["projectId"]))
        convert_to_csv(get_iam,project["projectId"])
    print(f"File generated in: {csv_file_path}")

main()