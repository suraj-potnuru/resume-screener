"""
Qdrant Service Module
Handles embedding generation using Google Gemini and storage/retrieval in Qdrant vector database.
"""
import os
import uuid
import re
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from google import genai

class QdrantService: #pylint: disable=R0902
    """
    Qdrant Service Module
    Handles embedding generation using Google Gemini and
    storage/retrieval in Qdrant vector database.
    """
    def __init__(self):
        """
        Initialize QdrantService with configuration from environment variables.
        """
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = "resumes"
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")  # set this env var with your key
        self.embed_model = "gemini-embedding-001"          # recommended model
        self.default_vector_size = 1536
        self.chunks = []
        self.points = []
        self.qclient = QdrantClient(url=self.qdrant_url)
        self.genai_client = genai.Client(api_key=self.gemini_api_key)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Google Gemini embedding model.
        """
        # genai python example: client.models.embed_content(...)
        res = self.genai_client.models.embed_content(model=self.embed_model, contents=texts)
        # res.embeddings is a list of vectors
        return res.embeddings

    def ensure_collection(self, name: str, vector_size: int):
        """
        Ensure that a Qdrant collection exists with the specified name and vector size.
        If it does not exist, create it.
        """
        # If collection exists we keep it; to recreate, use recreate_collection
        if name in [c.name for c in self.qclient.get_collections().collections]:
            print(f"Collection {name} already exists.")
            return
        self.qclient.recreate_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )
        print(f"Created collection {name} with vector size {vector_size}.")

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text by removing unwanted characters and normalizing whitespace.
        """
        if not text:
            return ""
        # Normalize whitespace, remove weird bullets, collapse newlines
        text = re.sub(r"[•\u2022]", "-", text)   # convert bullet characters
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def prepare_resume_chunks(self, resume_json: Dict) -> List[Dict]:
        """
        Prepare resume chunks from the extracted resume JSON for embedding.
        Each chunk corresponds to a section of the resume (summary, skills, experience, education).
        """
        self.chunks = []  # reset chunks
        rid = resume_json["resume_id"]
        data = resume_json["extracted_data"]
        rname = data.get("name", "").strip()
        summary = self._clean_text(data.get("summary", ""))
        if summary:
            self.chunks.append({
                "id": str(uuid.uuid4()),
                "text": f"[SUMMARY] {summary}",
                "metadata": {
                    "resume_id": rid,
                    "candidate_name": rname,
                    "section": "summary"
                }
            })
        for s in data.get("skills", []):
            skill = self._clean_text(s)
            if not skill:
                continue
            self.chunks.append({
                "id": str(uuid.uuid4()),
                "text": f"[SKILL] {skill}",
                "metadata": {
                    "resume_id": rid,
                    "candidate_name": rname,
                    "section": "skill",
                    "skill": skill
                }
            })
        for exp in data.get("experience", []):
            role = self._clean_text(exp.get("role", ""))
            company = self._clean_text(exp.get("company", ""))
            start = exp.get("start_date")
            end = exp.get("end_date")
            desc = self._clean_text(exp.get("description", ""))
            text_parts = []
            if role or company:
                text_parts.append(f"{role} at {company}")
            if start or end:
                text_parts.append(f"({start} - {end})")
            if desc:
                text_parts.append(desc)
            full_text = " ".join(text_parts).strip()
            if full_text:
                self.chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": f"[EXPERIENCE] {full_text}",
                    "metadata": {
                        "resume_id": rid,
                        "candidate_name": rname,
                        "section": "experience",
                        "company": company,
                        "role": role,
                        "start_date": start,
                        "end_date": end
                    }
                })
        for edu in data.get("education", []):
            degree = self._clean_text(edu.get("degree", ""))
            inst = self._clean_text(edu.get("institution", ""))
            start = edu.get("start_year")
            end = edu.get("end_year")
            text = f"{degree} at {inst}".strip()
            if start or end:
                text += f" ({start}-{end})"
            if text:
                self.chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": f"[EDUCATION] {text}",
                    "metadata": {
                        "resume_id": rid,
                        "candidate_name": rname,
                        "section": "education",
                        "institution": inst,
                        "degree": degree,
                        "start_year": start,
                        "end_year": end
                    }
                })

    def create_embeddings_and_store(self):
        """
        Create embeddings for the chunks and store them in the Qdrant collection.
        """
        texts = [c["text"] for c in self.chunks]
        embeddings = self.embed_texts(texts)
        vec_len = len(embeddings[0].values)
        self.ensure_collection(self.collection_name, vec_len)
        # Build points
        for c, vec in zip(self.chunks, embeddings):
            pid = str(uuid.uuid4())
            payload = c["metadata"]
            payload["text"] = c["text"][:1000]  # store a text preview (avoid huge payloads)
            self.points.append(qmodels.PointStruct(id=pid, vector=vec.values, payload=payload))
            # upsert
            self.qclient.upsert(collection_name=self.collection_name, points=self.points)
            print(f"Upserted {len(self.points)} points to {self.collection_name}.")

    def semantic_search(self, query: str, limit: int = 5):
        """
        Perform a semantic search on the specified Qdrant collection using the query string.
        Returns the top results based on similarity.
        """
        q_emb = self.embed_texts([query])[0].values
        res = self.qclient.query_points(
            collection_name=self.collection_name,
            query=q_emb
        )
        results = []
        for point in res.points:
            results.append({
                "id": point.id,
                "score": point.score,
                "payload": point.payload
            })
        return results[:limit]