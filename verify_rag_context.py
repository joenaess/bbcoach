import sys
import os


# Mock Streamlit
class MockStreamlit:
    def markdown(self, text):
        print(f"[ST.MARKDOWN] {text}")

    def expander(self, label, expanded=False):
        print(f"[ST.EXPANDER] {label}")
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def container(self):
        return self


sys.modules["streamlit"] = MockStreamlit()
import streamlit as st

# Add src to path
sys.path.append(os.path.abspath("src"))

from bbcoach.rag.pipeline import RAGPipeline


def main():
    print("Testing RAG Context Injection...")
    prompt = "How to improve free throw shooting?"
    context = "System Prompt..."

    try:
        pipeline = RAGPipeline()
        # Get top 3 results
        results = pipeline.query(prompt, n=3)

        if results and results["documents"] and results["documents"][0]:
            print(f"Found {len(results['documents'][0])} documents.")

            rag_context = (
                "\n=== KNOWLEDGE BASE RESOURCES (Breakthrough Basketball) ===\n"
            )
            rag_context += "Use the following drills or plays to answer the user's question if relevant:\n\n"

            # Store metadata to show to user
            used_resources = []

            message_placeholder = MockStreamlit()

            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                title = meta.get("title", "Untitled")
                url = meta.get("url", "#")
                rag_context += f"Resource {i + 1}: {title}\nContent: {doc[:100]}...\n\n"  # Truncated for print
                used_resources.append({"title": title, "url": url})

            context += rag_context

            # Show the user what we found
            print("\n--- Context Added ---\n")
            print(rag_context)

            print("\n--- UI Feedback ---\n")
            with message_placeholder.container():
                with st.expander("📚 Consulted Knowledge Base", expanded=False):
                    for res in used_resources:
                        st.markdown(f"- [{res['title']}]({res['url']})")
        else:
            print("No documents found.")

    except Exception as e:
        print(f"RAG Error: {e}")


if __name__ == "__main__":
    main()
