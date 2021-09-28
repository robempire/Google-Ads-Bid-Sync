"""
The script below was developed to take keyword bids from one Google Ads account, adjust them by
a fixed percentage, and use them as bids for the same keywords (in theoretically mirrored
ad groups) in a second account. This is handy to have if you are running multiple Google Ads
accounts (in alignment with Google Ads TOS) with the same keywords, but want to keep one
bid X% lower than the other, regardless of what adjustments you make to the main account.
Ad groups being used to broadcast or receive these bids can be defined simply by applying
a label to them in the UI or Ads Editor and taking note of the Label ID.

-----

Becuase of how thin Google Ads API documentation is, and due to deadlines involved, this
script was quite obviously developed for function, and not for beauty.

The long list of variables requested at the top are all required. Additionally, for auth
with the googleads/adwords library, you'll need to download, fill out, and store a YAML file.

-- You can find a template here:
    
https://github.com/googleads/google-ads-python/blob/master/google-ads.yaml

-- For generating refresh tokens, once an OAuth token has been acquired, use the following:

https://github.com/googleads/googleads-python-lib/blob/master/examples/adwords/authentication/generate_refresh_token.py

-- You may also want to keep handy a copy of my Google Ads API resources, especially if you
plan to modify this script (very doable):
    
https://github.com/robempire/google-ads-api-resources

"""

import sys
import pandas as pd
from googleads import adwords

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


_DEFAULT_PAGE_SIZE = 1000 # Leave as-is

PCT_ADJUST = 0.55 # The Max CPC adjustment to make between the main and inheriting accounts.


FROM_ACCOUNT_ID = 12345 # ID of account being drawn from
FROM_ADGROUP_LABEL = 'abc123' # Label applied to ad groups being drawn from (eg. '/labels/11354662779')
FROM_CAMPAIGN_PREFIX = 'No 1 - ' # Prefix on campaign names in account being drawn from (eg. 'No. 1 - My Campaign')
FROM_ADGROUP_SUFFIX = '_1' # Suffix on name of the ad group being transfered to
FROM_ACCOUNT_ALIAS = 'Account 1' # A name for the account being drawn from

TO_ACCOUNT_ID = 12345 # ID of account being drawn from
TO_ADGROUP_LABEL = 'abc123' # Label applied to ad groups being transfered to
TO_CAMPAIGN_PREFIX = 'No 2 - ' # Prefix on campaign names in account being transfered to
TO_ADGROUP_SUFFIX = '_2' # Suffix on name of the ad group being transfered to
TO_ACCOUNT_ALIAS = 'Account 2' # A name for the account being transfered to

LOGIN_CUSTOMER_ID = '1234567890' # When using this at the MCC level, this will be the ID of the "to" account

DEVELOPER_TOKEN = 'XyZ123' # Your API developer token
REFRESH_TOKEN = '1//a1b2c3d4f5' # Your auth refresh token
CLIENT_ID = 'somethingsomethingapps.googleusercontent.com' # Client ID
CLIENT_SECRET = '08642qwerty' # Your client secret

YAML_PATH = '/Path/to/your/google-ads.yml'

from_df = pd.DataFrame(columns=['keyword_text', 
                           'match_type', 
                           'cpc_bid', 
                           'criterion_id',
                           'criterion_status',
                           'ad_group_name',
                           'ad_group_id',
                           'campaign_id'], dtype='str')

to_df = from_df.copy()

mt_dict = {0:'UNSPECIFIED',
           1:'UNKNOWN',
           2:'EXACT',
           3:'PHRASE',
           4:'BROAD'}

account_dict = [
    {
     'account_alias':FROM_ACCOUNT_ALIAS, 'account_id':str(FROM_ACCOUNT_ID), 
     'campaign_prefix':FROM_CAMPAIGN_PREFIX, 'adgroup_suffix':FROM_ADGROUP_SUFFIX,
     'adgroup_label':FROM_ADGROUP_LABEL
     },
     
    {
     'account_alias':TO_ACCOUNT_ALIAS, 'account_id':str(TO_ACCOUNT_ID), 
     'campaign_prefix':TO_CAMPAIGN_PREFIX, 'adgroup_suffix':TO_ADGROUP_SUFFIX,
     'adgroup_label':TO_ADGROUP_LABEL
     }
    ]



def update_bids(client, ad_group_id, criterion_id, bid, adj_percent):
  # Initialize criterion service
  ad_group_criterion_service = client.GetService(
      'AdGroupCriterionService', version='v201809')
  
  # Construct operations and update bids.
  
  bid = str(int(round(bid-(bid * adj_percent), 2)*(10 ** 6)))
  
  operations = [{
      'operator': 'SET',
      'operand': {
          'xsi_type': 'BiddableAdGroupCriterion',
          'adGroupId': ad_group_id,
          'criterion': {
              'id': criterion_id,
          },
          'biddingStrategyConfiguration': {
              'bids': [
                  {
                      'xsi_type': 'CpcBid',
                      'bid': {
                          'microAmount': bid
                      }
                  }
              ]
          }
      }
  }]
  
  ad_group_criteria = ad_group_criterion_service.mutate(operations)

def main(df, ag_label, client, customer_id, page_size, ad_group_id=None):
    global from_df, to_df
    ga_service = client.get_service("GoogleAdsService")
    

    query = """
        SELECT
          ad_group.id,
          ad_group_criterion.type,
          ad_group_criterion.criterion_id,
          ad_group_criterion.keyword.text,
          ad_group_criterion.keyword.match_type,
          ad_group_criterion.cpc_bid_micros,
          ad_group_criterion.negative,
          ad_group_criterion.status,
          ad_group.name,
          ad_group.labels,
          ad_group.campaign
        FROM ad_group_criterion
        WHERE ad_group_criterion.type = KEYWORD
        AND ad_group_criterion.status = ENABLED
        AND ad_group_criterion.negative = FALSE
        AND ad_group.status = ENABLED
        AND ad_group.labels CONTAINS ALL ('customers/""" + customer_id + ag_label + """')"""


    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = customer_id
    request.query = query
    request.page_size = page_size

    results = ga_service.search(request=request)

    for row in results:
        ad_group = row.ad_group
        ad_group_criterion = row.ad_group_criterion
        keyword = row.ad_group_criterion.keyword
        
        # Clunky but effective way to build DFs from this loop
        
        if df == FROM_ACCOUNT_ALIAS:
            from_df = from_df.append({'keyword_text':keyword.text,
                            'match_type':mt_dict[keyword.match_type],
                            'cpc_bid':ad_group_criterion.cpc_bid_micros/1000000,
                            'criterion_id':str(ad_group_criterion.criterion_id),
                            'criterion_status':ad_group_criterion.status,
                            'ad_group_name':ad_group.name,
                            'ad_group_id':ad_group.id,
                            'campaign_id':ad_group.campaign.split('/')[-1]}, ignore_index=True)
        if df == TO_ACCOUNT_ALIAS:
            to_df = to_df.append({'keyword_text':keyword.text,
                            'match_type':mt_dict[keyword.match_type],
                            'cpc_bid':ad_group_criterion.cpc_bid_micros/1000000,
                            'criterion_id':str(ad_group_criterion.criterion_id),
                            'criterion_status':ad_group_criterion.status,
                            'ad_group_name':ad_group.name,
                            'ad_group_id':ad_group.id,
                            'campaign_id':ad_group.campaign.split('/')[-1]}, ignore_index=True)


        
if __name__ == "__main__":


    credentials = {
    "developer_token": DEVELOPER_TOKEN,
    "refresh_token": REFRESH_TOKEN,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "login_customer_id":LOGIN_CUSTOMER_ID}
    
    googleads_client = GoogleAdsClient.load_from_dict(credentials)
    for entry in account_dict:
        try:
            main(
                entry['account_alias'],
                entry['adgroup_label'],
                googleads_client,
                entry['account_id'],
                100,
                ad_group_id=None
            )
        except GoogleAdsException as ex:
            print(
                f'Request with ID "{ex.request_id}" failed with status '
                f'"{ex.error.code().name}" and includes the following errors:'
            )
            for error in ex.failure.errors:
                print(f'\tError with message "{error.message}".')
                if error.location:
                    for field_path_element in error.location.field_path_elements:
                        print(f"\t\tOn field: {field_path_element.field_name}")
            sys.exit(1)
        
    
    to_df['ag_strip'] = to_df['ad_group_name'].replace({f'\s.\s{TO_ADGROUP_SUFFIX}':''}, inplace=True, regex=True)
    
    ag_merge_df = pd.merge(from_df, to_df, left_on=['ad_group_name', 'keyword_text', 'match_type'], right_on=['ag_strip', 'keyword_text', 'match_type'], how='inner', suffixes=('_from', '_to'))
    
    ag_merge_df.drop_duplicates(inplace=True)
    
    adwords_client = adwords.AdWordsClient.LoadFromStorage(YAML_PATH)
    
    for idx, row in ag_merge_df.iterrows():
        try:
            update_bids(adwords_client, 
                        row['ad_group_id_to'], 
                        row['criterion_id_to'], 
                        row['cpc_bid_from'],
                        PCT_ADJUST)
        except Exception as e:
            print (e)
            continue
    
    