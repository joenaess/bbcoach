from bbcoach.rag.vector_store import VectorStore
import logging

logging.basicConfig(level=logging.ERROR)


def main():
    store = VectorStore()
    print(f"Total documents: {store.count()}")

    # Print a sample document
    results = store.query("drill", n_results=1)
    if results and results["documents"]:
        print("Sample document:")
        print(results["documents"][0][0][:200] + "...")


if __name__ == "__main__":
    main()
