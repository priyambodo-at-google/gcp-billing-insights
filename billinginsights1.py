# How to Run this Python Code:
# ============================
# $ rm -rf bill-env
# $ pip install virtualenv
# $ virtualenv bill-env
# $ source bill-env/bin/activate
# $ pip install -r requirements.txt

# $ python billinginsights1.py -pr <project_id> -se <standard_billing_ds> -bb <billinginsight_ds>
# <project id> --> fill this with your existing/current project ID 
# <standard billing ds> --> fill this with your existing/current standard billing dataset that you configure from billing
# <billinginsight_ds> --> dataset of your bigquery to store the view of the billing insight
# Example:
# $ python billinginsights1.py -pr biracaritdotcom-production -se bicaraitcom_dataset_billing_standard -bb bicaraitcom_dataset_billing_datastudio

# Verify that the view vw_gcpbillinginsights_standard already created in your selected dataset

from google.cloud import bigquery
from google.cloud import billing
from google.api_core.exceptions import PermissionDenied
from google.cloud.exceptions import NotFound
import argparse
import sys
from colorama import Back
from colorama import Style

bq_client = bigquery.Client()
app_version = "1.0"

# This function checks if vw_gcpbillinginsights_standard dataset already exists or not
# so that we are not recreating it
def check_vw_gcpbillinginsights_standard_dataset_exists(dataset_id):
    try:
        bq_client.get_dataset(dataset_id)  # Make an API request.
        print("Dataset {} already exists.".format(dataset_id))
        return True
    except NotFound:
        print("Dataset {} is not found.".format(dataset_id))
        return False

# Creates vw_gcpbillinginsights_standard dataset.
# Location is taken from the billing export table provided by the user.
def create_dataset(args):

    global detailedBBDataset
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
                                    args.vw_gcpbillinginsights_standard_DATASET_NAME_TO_BE_CREATED)
        create_dataset_by_location(dataset_id, standard_table_info.location)
    except NotFound:
        print("Table {} is not found check the export and proceed.".format(
            standard_source_id))
        # Standard is mandatory so program will fail if doesnot exists.
        sys.exit()

    print("Creating detailed Dataset.")

# Creates vw_gcpbillinginsights_standard dataset based on billing exported location
# Location is taken from the billing export table provided by the user.
def create_dataset_by_location(dataset_id, location):
    # Check if vw_gcpbillinginsights_standard dataset exists
    if check_vw_gcpbillinginsights_standard_dataset_exists(dataset_id) is True:
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


# Creates the view for the vw_gcpbillinginsights_standard
def create_vw_gcpbillinginsights_standard_view(args, isStandard):

    global output_url
    global detailedBBDataset

    if isStandard is True:
        source_id = "{}.{}.{}".format(args.PROJECT_ID,
                                      args.STANDARD_BILLING_EXPORT_DATASET_NAME,
                                      args.standard_table)
        view_id = "{}.{}.{}".format(args.PROJECT_ID,
                                    args.vw_gcpbillinginsights_standard_DATASET_NAME_TO_BE_CREATED,
                                    args.bb_standard)

    print('source_id={} and view_id={}'.format(source_id, view_id))

    # Standard -Fail view creation & url construct if standard is missing
    # Detailed -Skip view creation & url construct if detailed is missing.
    try:
        bq_client.get_table(source_id)
    except NotFound:
        if isStandard is True:
            print("Standard usage cost export not found=" + source_id +
                  " so skipping vw_gcpbillinginsights_standard view creation")
            sys.exit()
        return

    sql = """
    CREATE VIEW if not exists `{}`
    AS select *, COALESCE((SELECT SUM(x.amount) FROM UNNEST(s.credits) x),0) AS credits_sum_amount, COALESCE((SELECT SUM(x.amount) FROM UNNEST(s.credits) x),0) + cost as net_cost, EXTRACT(DATE FROM _PARTITIONTIME) AS date from `{}` s WHERE _PARTITIONTIME >'2020-08-01'
    """.format(view_id, source_id)

    # Not sure why this need project_id
    bq_view_client = bigquery.Client(project=args.PROJECT_ID)

    job = bq_view_client.query(sql)  # API request.
    job.result()  # Waits for the query to finish.

    print('Created view {}{}.{}.{}'.format(Back.GREEN, job.destination.project,
                                           job.destination.dataset_id,
                                           job.destination.table_id))
    print(Style.RESET_ALL)

def remove_vw_gcpbillinginsights_standard_dataset(args):
    standard_view_id = "{}.{}.{}".format(
        args.PROJECT_ID, args.vw_gcpbillinginsights_standard_DATASET_NAME_TO_BE_CREATED,
        args.bb_standard)
    bq_client.delete_table(standard_view_id, not_found_ok=True)
    print("vw_gcpbillinginsights_standard view {} deleted.".format(standard_view_id))
    return True

def main(argv):

    global detailedBBDataset
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
                        dest='vw_gcpbillinginsights_standard_DATASET_NAME_TO_BE_CREATED',
                        type=str,
                        required=True)
    parser.add_argument('-clean',
                        dest='clean',
                        type=str,
                        help='Only when you need cleanup, provide "yes"')

    args = parser.parse_args()
    print('Version of vw_gcpbillinginsights_standard.py  ' + app_version + "\n")

    # Detailed Export could be in different region so name will be modified as {}_detail in logic
    # So we are storing in global variable.
    detailedBBDataset = '{}'.format(args.vw_gcpbillinginsights_standard_DATASET_NAME_TO_BE_CREATED)

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
    args.bb_standard = "vw_gcpbillinginsights_standard"

    if args.clean is None:
        create_dataset(args)  # to create dataset
        create_vw_gcpbillinginsights_standard_view(args, True)  # to create standard view
    else:
        remove_vw_gcpbillinginsights_standard_dataset(args)  # to cleanup


# Main entry point
if __name__ == "__main__":
    main(sys.argv[1:])
