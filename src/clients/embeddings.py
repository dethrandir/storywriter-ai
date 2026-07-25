from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.repositories import repos
from openai import AsyncOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

qdrant = AsyncQdrantClient(host="localhost", port=7033)
openai_client = AsyncOpenAI(
    api_key="pa-W5t_s4tAc4fT809Vn4mM-C4eOI_Q9KEo03iTGufLE7B",
    base_url="https://api.voyageai.com/v1"
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""]
)


async def create_collection(collection_name: str) -> None:
    if not await qdrant.collection_exists(collection_name):
        await qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )


async def index(entity_type: str, entity_id: str, collection_name: str) -> None:
    repo = repos[entity_type]
    text = await repo.resolve_text(entity_id)
    if not text:
        return

    chunks = text_splitter.split_text(text)
    if not chunks:
        return

    embedding_response = await openai_client.embeddings.create(
        input=chunks,
        model="voyage-4-lite"
    )
    vectors = [d.embedding for d in embedding_response.data]

    points = [
        PointStruct(
            id=f"{entity_id}_chunk_{i}",
            vector=vector,
            payload={
                "text": chunk_text,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "chunk_index": i
            }
        )
        for i, (chunk_text, vector) in enumerate(zip(chunks, vectors))
    ]

    await qdrant.upsert(collection_name=collection_name, points=points)


async def get_context(input: str, collection_name: str) -> str:
    response = await openai_client.embeddings.create(
        input=input,
        model="voyage-4-lite"
    )

    search_results = await qdrant.search(
        collection_name=collection_name,
        query_vector=response.data[0].embedding,
        # query_filter=Filter(must=[""])
        limit=5
    )

    context_texts = [hit.payload.get("text", "") for hit in search_results]
    return "\n\n---\n\n".join(context_texts)