# gcp-billing-insights
gcp-billing-insights is a mechanism to monitor your billing through bigquery and dashboards. This is to create dataset and view for the project.
Open chrome browser and click this link to Open the cloudshell in your project &  Clone the project to create the view

Click this link:
https://console.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/priyambodo-at-google/gcp-billing-insights&cloudshell_tutorial=README.md 

Run this command:

rm -rf bill-env
pip install virtualenv
virtualenv bill-env
source bill-env/bin/activate
pip install -r requirements.txt

<project id> --> fill this with your existing/current project ID 
<standard billing ds> --> fill this with your existing/current standard billing dataset that you configure from billing
<billinginsight_ds> --> dataset of your bigquery to store the view of the billing insight
python billinginsights1.py -pr <project_id> -se <standard_billing_ds> -bb <billinginsight_ds>

Example:
python billinginsights1.py -pr core-billing -se my_priyambodo_argolis_billing_export -bb my_priyambodo_argolis_billing_billboard
