from freshrss_api import FreshRSSAPI
import json
import sqlite3
import urllib.parse
import os
import math

def convert_to_json(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM articles a JOIN statuses s ON a.articleID = s.articleID LEFT JOIN authorsLookup al ON a.articleID = al.articleID LEFT JOIN authors au ON al.authorID = au.authorID WHERE s.starred = 1")
    columns = [description[0] for description in cur.description]
    results = []
    for row in cur.fetchall():
        result = dict(zip(columns, row))
        results.append(result)
    conn.close()
    return json.dumps(results, indent=4)

def normalize_url (url):
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.netloc.lower()
    if hostname.startswith('www.'):
        hostname = hostname[4:]
    path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
    normalized = urllib.parse.urlunparse((
        'https',
        hostname,
        path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
    return normalized

with open('config.json') as f:
    config = json.load(f)

username = config['username']
client = FreshRSSAPI(
    host=config['host'],
    username=username,
    password=config['password'],
    verify_ssl=False,
    verbose=False
)

feeds = client.get_feeds()
feed_by_url = {normalize_url(feed["url"]): feed for feed in feeds["feeds"]}

database = json.loads(convert_to_json('DB.sqlite3'))

items = []
null_origin_items = []

for i in database:
    import_dateArrived = i["dateArrived"]
    import_published = i["datePublished"]
    import_url = i["url"] or i["externalURL"]
    import_title = i["title"]
    import_feedID = i["feedID"]
    import_contentHTML = i["contentHTML"]
    import_uniqueID = i["uniqueID"]
    import_name = i["name"]
    
    normal_url = normalize_url(import_feedID)
    feed_id = feed_by_url.get(normal_url, {}).get("id")
    feed_siteUrl = feed_by_url.get(normal_url, {}).get("site_url")
    feed_siteTitle = feed_by_url.get(normal_url, {}).get("title")

    item = {
        "crawlTimeMsec": str(int(import_dateArrived * (10 ** 3))),
        "timestampUsec": str(int(import_dateArrived * (10 ** 6))),
        "published": import_published,
        "title": import_title,
        "canonical": [
            {
                "href": import_url
            }
        ],
        "alternate": [
            {
                "href": import_url,
                "type": "text/html"
            }
        ],
        "categories": [
            "user/-/state/com.google/reading-list",
            "user/-/state/com.google/read",
            "user/-/state/com.google/starred",
        ],
        "origin": {
            "streamId": f"feed/{feed_id}",
            "htmlUrl": feed_siteUrl,
            "title": feed_siteTitle,
            "feedUrl": import_feedID
        },
        "content": {
            "content": f'{import_contentHTML}'
        },
        "guid": import_uniqueID,
        "author": import_name
    }
    items.append(item)

    if feed_id is None:
        null_origin_items.append({
            "title": import_title,
            "href": import_url,
            "feedUrl": import_feedID
        })

batch_size = 100
total_batches = math.ceil(len(items) / batch_size)

output_dir = "freshrss_export"
os.makedirs(output_dir, exist_ok=True)

if null_origin_items:
    print(f"\nWarning: {len(null_origin_items)} items have missing feed information")
    print(f"Warning: Exported feeds to compare")
    with open(os.path.join(output_dir, "export_feeds.json"), 'w') as json_file:
        json.dump(feeds, json_file, indent=4)
    print("These feedUrls could not be matched with FreshRSS feeds:")

    for item in null_origin_items:
        print(f"  Title: {item['title']}")
        print(f"  Article: {item['href']}")
        print(f"  Feed URL: {item['feedUrl']}\n")

print(f"Processing {len(items)} total items into {total_batches} files...")

for batch_num in range(total_batches):
    start_idx = batch_num * batch_size
    end_idx = min(start_idx + batch_size, len(items))
    batch_items = items[start_idx:end_idx]

    batch_result = {
        "id": f"user/{username}/state/org.freshrss/starred",
        "title": "List of favourite articles",
        "author": username,
        "items": batch_items
    }

    filename = f"starred_articles_batch_{batch_num + 1:03d}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w') as json_file:
        json.dump(batch_result, json_file, indent=4)

    print(f"Created {filename} with {len(batch_items)} items")

summary = {
    "export_info": {
        "total_items": len(items),
        "total_batches": total_batches,
        "batch_size": batch_size,
        "null_origin_count": len(null_origin_items)
    },
    "files": [f"starred_articles_batch_{i+1:03d}.json" for i in range(total_batches)],
    "null_origin_items": null_origin_items
}

summary_filepath = os.path.join(output_dir, "export_summary.json")
with open(summary_filepath, 'w') as json_file:
    json.dump(summary, json_file, indent=4)

print(f"\nExport completed!")
print(f"Total files created: {total_batches + 1} (including summary)")
print(f"Output directory: {output_dir}")
print(f"Items with null origin: {len(null_origin_items)}")
