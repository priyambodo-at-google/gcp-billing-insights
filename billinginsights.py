# Step by Step for you to run this:
# =================================
# Open this link in the browser to open cloudshell and clone the project.
# https://console.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/GoogleCloudPlatform/professional-services&cloudshell_tutorial=examples/billboard/billboard-walkthrough.md 
# https://console.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/priyambodo-at-google/gcp-billing-insights&cloudshell_tutorial=README.md 
#
# rm -rf bill-env
# pip install virtualenv
# virtualenv bill-env
# source bill-env/bin/activate
# pip install -r requirements.txt
# python billinginsights.py -h
#
# python billinginsights.py -pr <project_id> -se <standard_billing_ds> -bb <billinginsight_ds>
# <project id> --> fill this with your existing/current project ID 
# <standard billing ds> --> fill this with your existing/current standard billing dataset that you configure from billing
# <billinginsight_ds> --> dataset of your bigquery to store the view of the billing insight
# Example:
# python billinginsights.py -pr core-billing -se my_priyambodo_argolis_billing_export -bb my_priyambodo_argolis_billing_billboard
# OR
# python billinginsights.py -pr biracaritdotcom-production -se bicaraitcom_dataset_billing_standard -bb bicaraitcom_dataset_billing_datastudio
#
# Explore the datastudio dashboard and explore your billing by clicking the link which was the output of the script:
# ex: https://datastudio.google.com/reporting/949b9d13-3cc3-486e-beb7-ec9919a62288/page/vSVyB 

from google.cloud import bigquery
from google.cloud import billing
from google.api_core.exceptions import PermissionDenied
from google.cloud.exceptions import NotFound
import argparse
import sys
from colorama import Back
from colorama import Style

bq_client = bigquery.Client()

base_url = "https://datastudio.google.com/reporting/create?"
#report_part_url = base_url + "c.reportId=2e2ea000-8f68-40e2-8847-b80f05069b6e"
report_part_url = base_url + "c.reportId=c503be1b-f204-4141-adfe-0364491ebfd1"
report_base_url = report_part_url + "&r.reportName=BillingInsights"

std_proj_url = "&ds.ds39.connector=bigQuery&ds.ds39.projectId={}"
std_table_url = "&ds.ds39.type=TABLE&ds.ds39.datasetId={}&ds.ds39.tableId={}"
standard_view_url = std_proj_url + std_table_url

output_url = ""
app_version = "2.0"


# This function checks if billboard dataset already exists or not
# so that we are not recreating it
def check_billboard_dataset_exists(dataset_id):
    try:
        bq_client.get_dataset(dataset_id)  # Make an API request.
        print("Dataset {} already exists.".format(dataset_id))
        return True
    except NotFound:
        print("Dataset {} is not found.".format(dataset_id))
        return False


# Creates billboard dataset.
# Location is taken from the billing export table provided by the user.
def create_dataset(args):

    standard_source_id = "{}.{}.{}".format(
        args.PROJECT_ID, args.STANDARD_BILLING_EXPORT_DATASET_NAME,
        args.standard_table)

    standard_table_info = None

    print("Creating standard Dataset.")
    try:
        standard_table_info = bq_client.get_table(standard_source_id)
        print("Exported {} in GEO Location={}".format(
            standard_source_id, standard_table_info.location))
        # Create dataset for BB for standard export.
        dataset_id = "{}.{}".format(args.PROJECT_ID,
                                    args.BILLBOARD_DATASET_NAME_TO_BE_CREATED)
        create_dataset_by_location(dataset_id, standard_table_info.location)
    except NotFound:
        print("Table {} is not found check the export and proceed.".format(
            standard_source_id))
        # Standard is mandatory so program will fail if doesnot exists.
        sys.exit()

# Creates billboard dataset based on billing exported location
# Location is taken from the billing export table provided by the user.
def create_dataset_by_location(dataset_id, location):
    # Check if billboard dataset exists
    if check_billboard_dataset_exists(dataset_id) is True:
        return
    # Since we need to create, construct a full
    # Dataset object to send to the API.
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = location
    # Send the dataset to the API for creation, with an explicit timeout.
    # Raises google.api_core.exceptions.Conflict if the Dataset already
    # exist within the project.
    # Make an API request.
    dataset = bq_client.create_dataset(dataset, timeout=30)
    print("Created dataset {} on location {}".format(dataset_id, location))


# Creates the view for the Billboard
def create_billboard_view(args, isStandard):

    global output_url

    if isStandard is True:
        source_id = "{}.{}.{}".format(args.PROJECT_ID,
                                      args.STANDARD_BILLING_EXPORT_DATASET_NAME,
                                      args.standard_table)
        view_id = "{}.{}.{}".format(args.PROJECT_ID,
                                    args.BILLBOARD_DATASET_NAME_TO_BE_CREATED,
                                    args.bb_standard)

    print('source_id={} and view_id={}'.format(source_id, view_id))

    # Standard -Fail view creation & url construct if standard is missing
    try:
        bq_client.get_table(source_id)
    except NotFound:
        if isStandard is True:
            print("Standard usage cost export not found=" + source_id +
                  " so skipping billboard view creation")
            sys.exit()
        return

    sql = """
    CREATE VIEW if not exists `{}`
    AS select *, COALESCE((SELECT SUM(x.amount) FROM UNNEST(s.credits) x),0) AS credits_sum_amount, COALESCE((SELECT SUM(x.amount) FROM UNNEST(s.credits) x),0) + cost as net_cost, EXTRACT(DATE FROM _PARTITIONTIME) AS date from `{}` s WHERE _PARTITIONTIME >'2020-08-01'
    """.format(view_id, source_id)

    # Create the View
    bq_view_client = bigquery.Client(project=args.PROJECT_ID)
    job = bq_view_client.query(sql)  # API request.
    job.result()  # Waits for the query to finish.

    if isStandard is True:
        output_url = report_base_url + standard_view_url.format(
            args.PROJECT_ID, args.BILLBOARD_DATASET_NAME_TO_BE_CREATED,
            args.bb_standard)

    print('Created view {}{}.{}.{}'.format(Back.GREEN, job.destination.project,
                                           job.destination.dataset_id,
                                           job.destination.table_id))
    print(Style.RESET_ALL)


def generate_datastudio_url(args):
    print(
        "To view dataset, please click " + Back.GREEN +
        "https://console.cloud.google.com/bigquery", "\n")

    print(Style.RESET_ALL)

    print("To launch datastudio report, please click " + Back.GREEN +
          output_url + "\n")
    print(Style.RESET_ALL)


def remove_billboard_dataset(args):
    standard_view_id = "{}.{}.{}".format(
        args.PROJECT_ID, args.BILLBOARD_DATASET_NAME_TO_BE_CREATED,
        args.bb_standard)
    bq_client.delete_table(standard_view_id, not_found_ok=True)
    print("Billboard view {} deleted.".format(standard_view_id))
    return True


def main(argv):

    parser = argparse.ArgumentParser(
        description='Billing Export information, Version=' + app_version)
    parser.add_argument('-v',
                        action='version',
                        version='Version of %(prog)s ' + app_version)

    parser.add_argument('-pr',
                        dest='PROJECT_ID',
                        type=str,
                        help='Project Id',
                        required=True)
    parser.add_argument('-se',
                        dest='STANDARD_BILLING_EXPORT_DATASET_NAME',
                        type=str,
                        required=True)
    parser.add_argument('-bb',
                        dest='BILLBOARD_DATASET_NAME_TO_BE_CREATED',
                        type=str,
                        required=True)

    parser.add_argument('-clean',
                        dest='clean',
                        type=str,
                        help='Only when you need cleanup, provide "yes"')

    args = parser.parse_args()
    print('Version of billboard.py  ' + app_version + "\n")

    project_id_temp = "projects/{}".format(args.PROJECT_ID)
    try:
        project_billing_info = billing.CloudBillingClient(
        ).get_project_billing_info(name=project_id_temp)
    except PermissionDenied:
        print(
            "Permission Denied so you do not have project level permission or provided wrong project id, please check."
        )
        return sys.exit(1)

    billing_account_name = project_billing_info.billing_account_name.split(
        "/")[1]

    print("Project billing account=" + billing_account_name, "\n")
    args.standard_table = "gcp_billing_export_v1_" + \
        billing_account_name.replace('-', '_')
    args.bb_standard = "billboard"

    if args.clean is None:
        create_dataset(args)  # to create dataset
        create_billboard_view(args, True)  # to create standard view
        generate_datastudio_url(args)  # to create urls
    else:
        remove_billboard_dataset(args)  # to cleanup


# Main entry point
if __name__ == "__main__":
    main(sys.argv[1:])
