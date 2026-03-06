from rag.reasoner import rag_answer
from rag.loader import load_vector_store

stored = load_vector_store()

answer = rag_answer("What is LSA Type 1?", stored)

print(answer)