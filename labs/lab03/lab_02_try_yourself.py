"""Activity 3.2 (Try It Yourself) - Scaling High-Volume Media Posts (10,000 Comments on Video/Image)
Analysis of the 16 MB BSON Limit and Implementation of the Bucket & Subset Patterns for Multimedia Posts.
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, banner, print_json
from bson import ObjectId, json_util
import bson


def print_scaling_analysis():
    print("=" * 85)
    print("ANALYSIS: WHY EMBEDDING 10,000 COMMENTS IN A MEDIA POST IS PROBLEMATIC")
    print("=" * 85)
    analysis = """
1. 16 MB BSON Document Size Limit:
   - MongoDB enforces a hard 16 MB limit per BSON document.
   - For a viral video or image post, if 10,000 comments average 1.5 KB each (user info,
     timestamps, timestamps in video e.g. '02:15', likes, badges), the document reaches
     ~15-20 MB, crashing writes with 'BSONObjectTooLarge'.

2. RAM Cache Thrashing (WiredTiger Engine):
   - Whenever a user requests the video/image post metadata (URL, resolution, duration),
     WiredTiger must load the entire multi-megabyte document into RAM. This rapidly evicts
     frequently accessed cache working sets and causes severe disk I/O bottlenecks.

3. Document Growth & Disk Fragmentation:
   - Continually appending new comments to the embedded array causes document resizing
     and memory fragmentation on disk.

4. Network & Client Over-fetching:
   - Reading the media post transfers 10,000 comments over the wire, even when the user
     only views the video player and the top 3 featured comments.

-------------------------------------------------------------------------------------
RECOMMENDED ARCHITECTURAL SOLUTION: HYBRID SUBSET + BUCKET PATTERN FOR MEDIA POSTS
-------------------------------------------------------------------------------------
- Subset Pattern: Embed the top 3-5 most recent/pinned comments directly inside the
  Video/Image Post document. The media player + initial comments load instantaneously in 1 read.
- Bucket Pattern: Group remaining comments into 'Bucket Documents' of 50-100 comments per
  bucket (e.g. post_id, bucket_page, count, comments: [...]).
- Result: Fast paged reads, bounded document sizes (<100 KB), and scalable to millions of comments.
"""
    print(analysis)
    print("=" * 85 + "\n")


def main():
    banner("Activity 3.2: High-Volume Media Post Scaling (Try It Yourself)")
    print_scaling_analysis()

    db = get_db("nosql_labs")
    posts_col = db["media_posts_hybrid_scale"]
    buckets_col = db["media_comment_buckets"]
    posts_col.drop()
    buckets_col.drop()

    # Step 1: Create a viral Video post with Subset Pattern (recent/pinned comments embedded)
    post_id = ObjectId()
    initial_recent_comments = [
        {"author": "Creator_Pinned", "text": "4K 60FPS version uploaded! Timeline bookmarks in description.", "video_timestamp": "00:00", "likes": 1250},
        {"author": "TechReviewer", "text": "Insane latency benchmarks at 03:45!", "video_timestamp": "03:45", "likes": 480},
        {"author": "AI_Engineer", "text": "What GPU cluster was used for this benchmark?", "video_timestamp": "01:20", "likes": 310}
    ]

    post_doc = {
        "_id": post_id,
        "title": "Viral 4K Video: Next-Gen AI Robotics & Autonomous Vision Demo",
        "media_type": "video",
        "media_url": "https://cdn.media.io/videos/viral_ai_robotics_4k.mp4",
        "author": "TechInsider",
        "duration_seconds": 960,
        "resolution": "3840x2160",
        "codec": "AV1",
        "fps": 60,
        "file_size_mb": 450.8,
        "total_views": 3500000,
        "total_comments_count": 10000,
        "recent_comments_subset": initial_recent_comments  # Subset pattern
    }
    posts_col.insert_one(post_doc)
    print(f"[OK] Inserted viral video post '{post_doc['title']}' with Subset Pattern (3 featured comments).")

    # Step 2: Populate 10,000 comments using the Bucket Pattern (100 buckets of 100 comments)
    TOTAL_COMMENTS = 10000
    BUCKET_SIZE = 100
    TOTAL_BUCKETS = TOTAL_COMMENTS // BUCKET_SIZE

    print(f"\n=== Simulating 10,000 Media Comments using Bucket Pattern ({TOTAL_BUCKETS} buckets of {BUCKET_SIZE} comments) ===")
    buckets_to_insert = []
    for bucket_idx in range(TOTAL_BUCKETS):
        bucket_comments = [
            {
                "comment_id": bucket_idx * BUCKET_SIZE + c_idx + 1,
                "author": f"Viewer_{bucket_idx * BUCKET_SIZE + c_idx + 1}",
                "text": f"Awesome footage at frame #{bucket_idx * BUCKET_SIZE + c_idx + 1}!",
                "video_timestamp": f"{(c_idx % 15):02d}:{(c_idx * 3 % 60):02d}",
                "likes": (c_idx * 11) % 150
            }
            for c_idx in range(BUCKET_SIZE)
        ]
        bucket_doc = {
            "post_id": post_id,
            "bucket_page": bucket_idx + 1,
            "count": len(bucket_comments),
            "comments": bucket_comments
        }
        buckets_to_insert.append(bucket_doc)

    start_t = time.time()
    buckets_col.insert_many(buckets_to_insert)
    insert_duration = (time.time() - start_t) * 1000
    print(f"[OK] Successfully inserted {TOTAL_COMMENTS} video comments across {TOTAL_BUCKETS} bucket documents in {insert_duration:.2f} ms.")

    # Create compound index on (post_id, bucket_page)
    buckets_col.create_index([("post_id", 1), ("bucket_page", 1)])
    print("[OK] Created compound index on (post_id, bucket_page).")

    # Step 3: Fast Initial Read (Subset Pattern)
    print("\n=== Read 1: Initial Fast Media Player Load (Subset Pattern - 0 Joins) ===")
    post_render = posts_col.find_one({"_id": post_id})
    post_bson_size = len(bson.BSON.encode(post_render))
    print(f"  Media: [{post_render['media_type'].upper()}] {post_render['title']}")
    print(f"  Stream URL: {post_render['media_url']} ({post_render['resolution']}, {post_render['fps']}fps)")
    print(f"  Total Comments Count: {post_render['total_comments_count']}")
    print(f"  Embedded Subset Preview: {len(post_render['recent_comments_subset'])} featured comments")
    for c in post_render['recent_comments_subset']:
        print(f"    - [{c['author']} @ {c['video_timestamp']}]: {c['text']} (Likes: {c['likes']})")
    print(f"  -> Video Post Document Size: {post_bson_size} bytes ({post_bson_size / 1024:.2f} KB - Far below 16MB limit!)")

    # Step 4: Paginated Read (Page 1 of comments from Bucket Pattern)
    print("\n=== Read 2: User scrolls down -> Fetch Page 1 (Bucket 1) ===")
    bucket_1 = buckets_col.find_one({"post_id": post_id, "bucket_page": 1})
    bucket_bson_size = len(bson.BSON.encode(bucket_1))
    print(f"  Bucket Page: {bucket_1['bucket_page']} | Comments in Bucket: {bucket_1['count']}")
    print(f"  First 3 comments in Page 1:")
    for c in bucket_1['comments'][:3]:
        print(f"    - Comment #{c['comment_id']} by {c['author']} @ {c['video_timestamp']}: '{c['text']}'")
    print(f"  -> Single Bucket Document Size: {bucket_bson_size} bytes ({bucket_bson_size / 1024:.2f} KB)")

    # Step 5: Paginated Read (Page 50 of comments)
    print("\n=== Read 3: User jumps to Page 50 (Bucket 50) ===")
    bucket_50 = buckets_col.find_one({"post_id": post_id, "bucket_page": 50})
    print(f"  Bucket Page: {bucket_50['bucket_page']} | Comment Range: #{bucket_50['comments'][0]['comment_id']} to #{bucket_50['comments'][-1]['comment_id']}")
    print(f"  Sample Comment: Comment #{bucket_50['comments'][0]['comment_id']} by {bucket_50['comments'][0]['author']} @ {bucket_50['comments'][0]['video_timestamp']}")

    # Export sample documents to JSON
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_02_try_yourself.json")
    export_payload = {
        "media_post_document_with_subset": post_render,
        "sample_media_comment_bucket_page_1": bucket_1,
        "sample_media_comment_bucket_page_50": bucket_50,
        "scaling_summary": {
            "total_comments": TOTAL_COMMENTS,
            "total_buckets": TOTAL_BUCKETS,
            "bucket_size": BUCKET_SIZE,
            "post_doc_size_bytes": post_bson_size,
            "bucket_doc_size_bytes": bucket_bson_size,
            "max_mongodb_doc_limit_bytes": 16 * 1024 * 1024
        }
    }
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(export_payload, indent=2))
    print(f"\n[OK] Exported scaled architectural dataset to '{os.path.basename(json_path)}'")

    banner("Activity 3.2 Complete")


if __name__ == "__main__":
    main()
