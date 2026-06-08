"""Minimal Apify REST API client (stdlib only — no new dependencies).

Runs an Apify actor and returns its dataset items. Used to scrape LinkedIn
hiring posts / jobs via Apify's servers + proxies (NOT the user's LinkedIn
login — that's the whole point: Apify isolates the account risk).

Auth: set APIFY_TOKEN in the environment (or pass token=). Get it from
https://console.apify.com/account/integrations.

Example:
    from apify_client import run_actor_sync
    items = run_actor_sync(
        "harvestapi/linkedin-post-search",
        {"queries": ["hiring product manager Pune"], "maxPosts": 50},
    )
"""
import os
import json
import urllib.request
import urllib.error

APIFY_BASE = "https://api.apify.com/v2"


def get_token(token=None):
    token = token or os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError(
            "APIFY_TOKEN not set. Run `export APIFY_TOKEN=apify_api_xxx` "
            "(get it at https://console.apify.com/account/integrations) "
            "or pass token= explicitly."
        )
    return token


def run_actor_sync(actor_id, run_input, token=None, timeout=600):
    """Run an actor synchronously and return its dataset items (list of dicts).

    actor_id may use '/' (e.g. 'harvestapi/linkedin-post-search'); it is
    converted to the API's '~' form automatically. Blocks until the run
    finishes (or `timeout` seconds), then returns the scraped items.
    """
    token = get_token(token)
    aid = actor_id.replace("/", "~")
    url = f"{APIFY_BASE}/acts/{aid}/run-sync-get-dataset-items?token={token}"
    body = json.dumps(run_input).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"Apify HTTP {e.code}: {detail}") from e


def list_actor_runs(actor_id, token=None, limit=5):
    """Return recent runs for an actor (for debugging / reusing a prior run)."""
    token = get_token(token)
    aid = actor_id.replace("/", "~")
    url = f"{APIFY_BASE}/acts/{aid}/runs?token={token}&limit={limit}&desc=true"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8")).get("data", {}).get("items", [])


def get_dataset_items(dataset_id, token=None):
    """Fetch items from an existing dataset (e.g. a run you already paid for)."""
    token = get_token(token)
    url = f"{APIFY_BASE}/datasets/{dataset_id}/items?token={token}&clean=true&format=json"
    with urllib.request.urlopen(url, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))
