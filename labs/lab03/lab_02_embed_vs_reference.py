"""Lab 3.2 - Migrate from Referenced to Embedded Design (Image & Video Media Posts)
Compare referenced (normalized) vs embedded (denormalized) patterns for multimedia posts.
Implements automated migration pipeline and database query comparison.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, banner, print_json
from bson import ObjectId, json_util


def main():
    banner("Lab 3.2: Embed vs Reference Migration (Image & Video Media Posts)")
    db = get_db("nosql_labs")

    # =========================================================================
    # STEP 1: CREATE REFERENCED DESIGN (Separate collections for media posts & comments)
    # =========================================================================
    print("=== STEP 1: Referenced Design (Normalized Media Posts & Comments) ===")
    posts_col = db["media_posts"]
    comments_col = db["media_comments"]
    posts_col.drop()
    comments_col.drop()

    # Insert 5 posts (Image and Video multimedia posts)
    media_posts_data = [
        {
            "title": "Generative AI Architecture Diagram",
            "media_type": "image",
            "media_url": "https://cdn.media.io/images/ai_architecture_hd.png",
            "author": "Arjun Mehta",
            "resolution": "3840x2160",
            "format": "PNG",
            "file_size_mb": 4.2,
            "tags": ["image", "diagram", "ai", "architecture"],
            "created_at": "2024-01-15"
        },
        {
            "title": "MongoDB 8.0 Sharding & Clustering Tutorial",
            "media_type": "video",
            "media_url": "https://cdn.media.io/videos/mongo_sharding_1080p.mp4",
            "author": "Sneha Reddy",
            "duration_seconds": 745,
            "resolution": "1920x1080",
            "codec": "H.264",
            "file_size_mb": 185.4,
            "tags": ["video", "tutorial", "mongodb", "sharding"],
            "created_at": "2024-01-20"
        },
        {
            "title": "Vector Search: HNSW vs IVF Indexing Infographic",
            "media_type": "image",
            "media_url": "https://cdn.media.io/images/vector_hnsw_chart.jpg",
            "author": "Kavya Nair",
            "resolution": "2048x1536",
            "format": "JPEG",
            "file_size_mb": 2.1,
            "tags": ["image", "infographic", "vector", "search"],
            "created_at": "2024-02-01"
        },
        {
            "title": "Distributed Consensus & 2PC Animation Walkthrough",
            "media_type": "video",
            "media_url": "https://cdn.media.io/videos/2pc_distributed_tx.mp4",
            "author": "Arjun Mehta",
            "duration_seconds": 420,
            "resolution": "1920x1080",
            "codec": "AV1",
            "file_size_mb": 98.0,
            "tags": ["video", "animation", "distributed", "consensus"],
            "created_at": "2024-02-10"
        },
        {
            "title": "Real-Time Fraud Graph Traversal Live Demo",
            "media_type": "video",
            "media_url": "https://cdn.media.io/videos/fraud_graph_demo.mp4",
            "author": "Rahul Kumar",
            "duration_seconds": 530,
            "resolution": "3840x2160",
            "codec": "HEVC",
            "file_size_mb": 320.5,
            "tags": ["video", "demo", "graph", "fraud"],
            "created_at": "2024-02-15"
        },
    ]
    post_result = posts_col.insert_many(media_posts_data)
    post_ids = post_result.inserted_ids
    print(f"  [OK] Inserted {len(post_ids)} media posts (images & videos) into 'media_posts' collection.")

    # Insert 10 comments (referenced to post_ids with media timestamp/feedback)
    comments_data = [
        {"post_id": post_ids[0], "author": "TechReader1", "text": "Crisp 4K resolution! Great diagram clarity.", "rating": 5},
        {"post_id": post_ids[0], "author": "DevGuru", "text": "Saved this infographic for my system design review.", "rating": 5},
        {"post_id": post_ids[1], "author": "MongoLover", "text": "Timestamp 04:15 explaining config servers was brilliant!", "rating": 5},
        {"post_id": post_ids[1], "author": "DataEngineer", "text": "Could you do a follow-up video on zone sharding?", "rating": 4},
        {"post_id": post_ids[2], "author": "AIResearcher", "text": "The visual comparison of recall vs latency is very clear.", "rating": 5},
        {"post_id": post_ids[2], "author": "CloudArchitect", "text": "High quality chart, easy to read on mobile.", "rating": 4},
        {"post_id": post_ids[3], "author": "SystemDesigner", "text": "The 2-Phase Commit animation at 02:30 is super helpful.", "rating": 5},
        {"post_id": post_ids[3], "author": "Student99", "text": "Smooth 60fps video quality, audio is crystal clear.", "rating": 5},
        {"post_id": post_ids[4], "author": "FinTechAnalyst", "text": "4K live traversal visualization looks amazing!", "rating": 5},
        {"post_id": post_ids[4], "author": "SecurityPro", "text": "Great demo on cyclic transaction detection.", "rating": 5},
    ]
    comments_col.insert_many(comments_data)
    print(f"  [OK] Inserted {len(comments_data)} comments into 'media_comments' collection.\n")

    # =========================================================================
    # STEP 2: QUERY USING $lookup (Referenced join)
    # =========================================================================
    print("=== STEP 2: Retrieve Media Post with Comments via $lookup Aggregation ===")
    target_post_id = post_ids[1]  # Video post
    lookup_pipeline = [
        {"$match": {"_id": target_post_id}},
        {
            "$lookup": {
                "from": "media_comments",
                "localField": "_id",
                "foreignField": "post_id",
                "as": "comments"
            }
        }
    ]
    referenced_post = list(posts_col.aggregate(lookup_pipeline))[0]
    print(f"  Media Post: [{referenced_post['media_type'].upper()}] '{referenced_post['title']}' by {referenced_post['author']}")
    print(f"  Media URL:  {referenced_post['media_url']} ({referenced_post['resolution']}, {referenced_post['file_size_mb']} MB)")
    print(f"  Retrieved {len(referenced_post['comments'])} Comments via $lookup:")
    for comment in referenced_post['comments']:
        print(f"    - [{comment['author']} | Rating: {comment['rating']}]: {comment['text']}")

    # =========================================================================
    # STEP 3: MIGRATE REFERENCED DESIGN TO EMBEDDED DESIGN
    # =========================================================================
    print("\n=== STEP 3: Automated Migration from Referenced to Embedded Design ===")
    embedded_col = db["media_posts_embedded"]
    embedded_col.drop()

    # Migration pipeline using $lookup and $out to create embedded collection
    migration_pipeline = [
        {
            "$lookup": {
                "from": "media_comments",
                "localField": "_id",
                "foreignField": "post_id",
                "pipeline": [
                    {"$project": {"_id": 0, "author": 1, "text": 1, "rating": 1}}
                ],
                "as": "comments"
            }
        },
        {"$out": "media_posts_embedded"}
    ]
    posts_col.aggregate(migration_pipeline)
    print(f"  [OK] Migration completed! Created 'media_posts_embedded' collection with {embedded_col.count_documents({})} documents.")

    # Retrieve post with comments from embedded collection
    embedded_post = embedded_col.find_one({"_id": target_post_id})
    print(f"\n  [Embedded] Post Title: [{embedded_post['media_type'].upper()}] '{embedded_post['title']}'")
    print(f"  [Embedded] Comments embedded directly: {len(embedded_post['comments'])}")
    for comment in embedded_post['comments']:
        print(f"    - [{comment['author']} | Rating: {comment['rating']}]: {comment['text']}")

    # =========================================================================
    # STEP 4: COMPARE NUMBER OF QUERIES & PERFORMANCE CHARACTERISTICS
    # =========================================================================
    print("\n=== STEP 4: Query Complexity & Design Comparison ===")
    print("  1. In Referenced Design:")
    print("     - Without $lookup: Requires 2 round-trip queries (1 to fetch media post, 1 to fetch comments by post_id).")
    print("     - With $lookup: 1 aggregation query, but server executes index joins / collection scan.")
    print("  2. In Embedded Design:")
    print("     - Exactly 1 simple primary key find query (db.media_posts.findOne({_id})). Zero joins, single disk read.")
    print()
    print(f"  {'Metric / Aspect':<25} {'Referenced Design':<28} {'Embedded Design':<25}")
    print(f"  {'-'*78}")
    print(f"  {'Queries needed (simple)':<25} {'2 separate queries':<28} {'1 single find() query':<25}")
    print(f"  {'Queries needed ($lookup)':<25} {'1 pipeline query':<28} {'1 single find() query':<25}")
    print(f"  {'Join Overhead':<25} {'Yes ($lookup join)':<28} {'None (pre-joined)':<25}")
    print(f"  {'Atomicity':<25} {'Multi-document / Transaction':<28} {'Single document (atomic)':<25}")
    print(f"  {'Document Growth':<25} {'None (fixed post size)':<28} {'Grows with each comment':<25}")
    print(f"  {'Best Use Case':<25} {'Unbounded 1:N relations':<28} {'Bounded 1:N relations (<100)':<25}")

    # Export collection to JSON
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_02_embed_vs_reference.json")
    all_embedded = list(embedded_col.find())
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(all_embedded, indent=2))
    print(f"\n[OK] Exported {len(all_embedded)} documents to '{os.path.basename(json_path)}'")

    banner("Lab 3.2 Complete")


if __name__ == "__main__":
    main()