from chromadb import EmbeddingFunction, Documents, Embeddings

from app.config import settings

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.embedding_model_name)
    return _model


class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        pass

    def __call__(self, input: Documents) -> Embeddings:
        model = get_embedding_model()
        vectors = model.encode(list(input), convert_to_numpy=True)
        return vectors.tolist()

    @staticmethod
    def name() -> str:
        return "sentence-transformer-local"
