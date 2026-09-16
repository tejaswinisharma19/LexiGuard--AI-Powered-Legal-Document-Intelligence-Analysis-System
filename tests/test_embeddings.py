from ai.embeddings import LexiGuardEmbeddings


documents = [
    "Either party may terminate the agreement by providing 30 days written notice.",
    "Payment shall be made within 15 days of receiving the invoice.",
    "The agreement shall automatically renew for one year."
]


embedding_model = LexiGuardEmbeddings()

embedding_model.create_embeddings(documents)

query = "How many days notice is required to terminate the agreement?"

query_vector = embedding_model.embed_query(query)

similarities = embedding_model.calculate_similarity(
    query_vector
)


print("Query:", query)

print("\nSimilarity scores:")

for index, score in enumerate(similarities):
    print(f"Document {index + 1}: {score:.4f}")


best_match_index = similarities.argmax()

print("\nMost relevant document:")
print(documents[best_match_index])