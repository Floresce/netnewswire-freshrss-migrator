# NetNewsWire to FreshRSS migration

A script to migrated starred articles from NetNewsWire to FreshRSS favourites. 

Tested with NetNewsWire 6.1.9 on iOS and FreshRSS 1.26.3

## Extracting articles database

This requires the database `DB.sqlite3` to be extracted from NetNewsWire [as discussed here](https://github.com/Ranchero-Software/NetNewsWire/issues/978#issuecomment-1320911427). iOS versions of NetNewsWire can be extracted from iOS computer backups. I have not tested with different versions of NetNewsWire other than iOS, but I would assume they are similar.

iCloud-sync articles DB location:
`~/Library/Containers/com.ranchero.NetNewsWireEvergreen/Data/Library/Application\Support/NetNewsWire/Accounts/2_iCloud/DB.sqlite3`

'On My Mac' articles DB location:
`~/Library/Containers/com.ranchero.NetNewsWireEvergreen/Data/Library/Application\Support/NetNewsWire/Accounts/OnMyMac/DB.sqlite3`

'On My iPhone' DB location:
`NetNewsWire/Container/Documents/Accounts/OnMyMac/DB.sqlite3`

## Config
In FreshRSS setting, enable API access under Settings > Administration > Authentication > Allow API access

Set API password under Settings > Account > Profile > External access via API > API password

Create a `config.json` file at the root directory next to the script:
```
{
    "host": "https://your-freshrss-server.com",
    "username": "your_username",
    "password": "your_password"
}
```
Add in your FreshRSS hostname and username, and use your API password for the `password` field.
For reference, [freshrss-api documentation](https://github.com/thiswillbeyourgithub/freshrss_python_api/) used to obtain list of feeds.

## Usage
Once the database file is obtained and configuration is set up, place it at the root directory along with the script and config file. 

IMPORTANT NOTE: Ensure that the subscriptions/feeds from NetNewsWire has been imported to FreshRSS, before running this script. This can be exported from NetNewsWire, which usually exports a file like `Subscriptions-OnMyiPhone.opml` and can be imported through FreshRSS on the left sidebar through Subscription management > Import / export > Import. FreshRSS must already have its feed setup, so that the script can compare your NetNewsWire's starred articles to match data.

Install Python
```bash
https://www.python.org/downloads/
```
Clone this repo
```bash
git clone https://github.com/Floresce/netnewswire-freshrss-migrator
```
Install requirements
```bash
pip install -r requirements.txt
```

Run this script
```bash
python starred_export.py
```

The script would export a list of files under `freshrss_export/`
```
freshrss_export/
    export_feeds.json (shows up if there is a problem, refer to 'Troubleshooting' section)
    export_summary.json
    starred_article_batch_XXX.json
```
If a warning message shows up, refer to the [Troubleshooting](#troubleshooting) section to correct the issue, before continuing.

With all the `starred_article_batch_XXX.json` files, in FreshRSS, navigate to the left sidebar to Subscription management > Import / export > Import, and import all those files one at a time.

After that, all of your starred articles from NetNewsWire should be imported to FreshRSS.

## Troubleshooting

If the output shows a warning that there are items that have missing feed information, this is due to the mismatch of feed URLs from the NetNewsWire's `DB.sqlite3` and the list of feeds from FreshRSS. This may be caused by the lack of subscriptions/feeds in FreshRSS that haven't been imported yet. But most likely, it might be caused by incorrect or outdated feed URLs from older starred articles. You would need to manually fix this for each item.

For example, I might have an item, like:
```bash
Warning: 1 items have missing feed information
Warning: Exported feeds to compare
These feedUrls could not be matched with FreshRSS feeds:
  Title: Twitter Has Stopped Working in NetNewsWire
  Article: https://netnewswire.blog/2023/04/07/twitter-has-stopped.html
  Feed URL: https://nnw.ranchero.com/feed.xml
```
If you lookup the item based on the given Title or Article in any of the `starred_articles_batch_XXX.json`, you will see null values in "origin" section, for example:
```json
"origin": {
    "streamId": "feed/None",
    "htmlUrl": null,
    "title": null,
    "feedUrl": "https://nnw.ranchero.com/feed.xml"
},
```
And, if you look up what the actual feed is in `export_feeds.json`:
```json
{
    "id": 20,
    "favicon_id": 20,
    "title": "NetNewsWire News",
    "url": "https://netnewswire.blog/feed.xml",
    "site_url": "https://netnewswire.blog/",
    "is_spark": 0,
    "last_updated_on_time": 1755323111
},
```
You correct this by matching with the appropriate values
* "streamId" -> "feed/{id}"
* "htmlUrl" -> "{site_url}"
* "title" -> "{title}"
* "feedUrl" -> "{url}"

Which would look something like this:
```json
"origin": {
    "streamId": "feed/20",
    "htmlUrl": "https://netnewswire.blog/",
    "title": "NetNewsWire News",
    "feedUrl": "https://netnewswire.blog/feed.xml"
},
```

After fixing the issue, DON'T run the script again, and continue back to the instructions.
