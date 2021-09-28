# Google-Ads-Bid-Sync
Sync and/or adjust keyword level bids between multiple Google Ads accounts via API

The script below was developed to take keyword bids from one Google Ads account, adjust them by
a fixed percentage, and use them as bids for the same keywords (in theoretically mirrored
ad groups) in a second account. This is handy to have if you are running multiple Google Ads
accounts (in alignment with Google Ads TOS) with the same keywords, but want to keep one
bid X% lower than the other, regardless of what adjustments you make to the main account.
Ad groups being used to broadcast or receive these bids can be defined simply by applying
a label to them in the UI or Ads Editor and taking note of the Label ID.

-----

Because of how thin Google Ads API documentation is, and due partially to deadlines involved, this
script was quite obviously developed for function, and not for beauty.

The long list of variables requested at the top are all required. Additionally, for auth
with the googleads/adwords library, you'll need to download, fill out, and store a YAML file.

You can find a template here:
    
https://github.com/googleads/google-ads-python/blob/master/google-ads.yaml

For generating refresh tokens, once an OAuth token has been acquired, use the following:

https://github.com/googleads/googleads-python-lib/blob/master/examples/adwords/authentication/generate_refresh_token.py

You may also want to keep handy a copy of my Google Ads API resources, especially if you
plan to modify this script (very doable):
    
https://github.com/robempire/google-ads-api-resources
