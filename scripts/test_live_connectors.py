"""
Test Suite for Live Scientific Connectors & Persistent Caching (scripts/test_live_connectors.py)
Validates OpenAlex, Crossref, SQLite Cache, and ECC expansion under live network queries.
"""

import sys
import os
import time
from app.icg.external_search import (
    OpenAlexClient, CrossrefClient, SemanticScholarClient,
    ScientificPaperCache, ExternalSearchEngine
)


def test_live_connectors():
    print("=" * 80)
    print("  LIVE SCIENTIFIC CONNECTORS & SQLITE CACHE VERIFICATION")
    print("=" * 80)

    # 1. Test OpenAlex API
    print("\n[1/5] Testing Live OpenAlex API...")
    oa = OpenAlexClient()
    oa_res = oa.search_works("quantum error correction surface codes", limit=2)
    print(f"      OpenAlex Results Found: {len(oa_res)}")
    for r in oa_res:
        print(f"      - [{r['id']}] {r['title'][:60]}... ({r['year']}, Citations: {r['citations']})")
    assert len(oa_res) > 0, "OpenAlex returned 0 results"

    # 2. Test Crossref API
    print("\n[2/5] Testing Live Crossref API...")
    cr = CrossrefClient()
    cr_res = cr.search_works("graphene oxide water purification", limit=2)
    print(f"      Crossref Results Found: {len(cr_res)}")
    for r in cr_res:
        print(f"      - [{r['id']}] {r['title'][:60]}... (DOI: {r['doi']})")
    assert len(cr_res) > 0, "Crossref returned 0 results"

    # 3. Test Persistent SQLite Cache Layer
    print("\n[3/5] Testing Persistent SQLite Cache Layer...")
    test_db = "data/test_papers_cache.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    cache = ScientificPaperCache(db_path=test_db)
    cache.save_paper(
        paper_id="TEST_001",
        source="unit_test",
        title="Deep Reinforcement Learning in Robotics",
        claim="Proximal policy optimization stabilizes robot gait on uneven terrain.",
        abstract="Full abstract text...",
        discipline="Robotics",
        language="en",
        year=2025,
        keywords=["robot", "ppo", "reinforcement"]
    )
    
    cached_doc = cache.get_paper("TEST_001")
    assert cached_doc is not None, "Failed to retrieve saved paper from cache"
    print(f"      Successfully cached and retrieved: {cached_doc['title']} (Source: {cached_doc['source']})")

    # 4. Test Full ExternalSearchEngine with Live Search & Auto-Cache
    print("\n[4/5] Testing ExternalSearchEngine Multi-Source Live Search & Auto-Cache...")
    engine = ExternalSearchEngine(enable_live_search=True, cache_db_path=test_db)
    initial_ecc = engine.calculate_ecc("Medicine")
    print(f"      Initial ECC: {initial_ecc:.3f}")

    live_papers = engine.search_live_scientific_corpus("mRNA vaccine lipid nanoparticle delivery", discipline="Medicine", top_k=3)
    print(f"      Live Papers Ingested & Cached: {len(live_papers)}")
    new_ecc = engine.calculate_ecc("Medicine")
    print(f"      Updated Grounded ECC: {new_ecc:.3f} (Expanded by {new_ecc - initial_ecc:+.3f})")
    assert new_ecc >= initial_ecc, "ECC should increase as external evidence is indexed"

    # 5. Test Cache Hit Speed (Instant replay without network)
    print("\n[5/5] Testing Cache Hit Replay Speed...")
    t0 = time.time()
    replayed = engine.search_live_scientific_corpus("mRNA vaccine lipid nanoparticle delivery", discipline="Medicine", top_k=3)
    t_delta = (time.time() - t0) * 1000
    print(f"      Cache Hit Retrieval: {len(replayed)} items in {t_delta:.2f} ms")
    assert len(replayed) == len(live_papers), "Cache replay should return all saved items"
    assert t_delta < 50.0, "Cache replay must be instant (<50ms)"

    print("\n" + "=" * 80)
    print("  ALL LIVE SCIENTIFIC CONNECTORS & CACHE TESTS PASSED SUCCESSFULLY (5/5)!")
    print("=" * 80)


if __name__ == "__main__":
    test_live_connectors()
