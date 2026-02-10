from bbcoach.rag.pipeline import RAGPipeline
import logging

logging.basicConfig(level=logging.INFO)


def main():
    pipeline = RAGPipeline()
    pipeline.reset_db()

    # Start from the drills hub
    start_urls = [
        "https://www.breakthroughbasketball.com/drills/basketballdrills.html",
    ]

    print("Starting ingestion (max 20 pages)...")
    # Increase pages to ensure we get some drills
    count = pipeline.run_ingestion(start_urls, max_depth=1, max_pages=20)
    print(f"Ingested {count} chunks.")

    print("Testing query...")
    results = pipeline.query("How to improve shooting?")
    if results and results["documents"]:
        print(f"Found {len(results['documents'][0])} results.")
        print("Top result snippet:")
        print(results["documents"][0][0][:300])
    else:
        print("No results found.")


if __name__ == "__main__":
    main()
