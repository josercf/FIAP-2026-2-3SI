"""
LogiTech Enterprise - Exemplo Didático RAG + pgvector
Aula 12 - Persistência Vetorial e Model Context Protocol
"""

import numpy as np

# MOCK: Simulação de embeddings gerados por uma LLM (ex: text-embedding-ada-002)
mock_database = [
    {"id": 1, "text": "Caminhão parado na rodovia Dutra por problema no motor.", "vector": np.array([0.1, 0.8, 0.2])},
    {"id": 2, "text": "Entrega realizada com sucesso no cliente em SP.", "vector": np.array([0.9, 0.1, 0.1])},
    {"id": 3, "text": "Atraso no frete devido a chuvas fortes no sul.", "vector": np.array([0.2, 0.7, 0.9])}
]

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def retrieve_context(query_vector, top_k=1):
    """
    Etapa de Retrieval (Busca Vetorial por Similaridade)
    Simula uma query no pgvector usando a distância de cosseno.
    """
    results = []
    for doc in mock_database:
        score = cosine_similarity(query_vector, doc["vector"])
        results.append((score, doc))
    
    # Ordena pelo maior score e pega os top_k
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_k]

def generate_response(query_text, context):
    """
    Etapa de Generation (RAG)
    Simula o envio do contexto resgatado + a query do usuário para a LLM.
    """
    prompt = f"""
Você é o assistente IA da LogiTech Enterprise.
Utilize o CONTEXTO abaixo para responder à PERGUNTA.

CONTEXTO:
{context}

PERGUNTA:
{query_text}

RESPOSTA:
"""
    # MOCK da resposta da LLM
    print("\n--- PROMPT ENVIADO À LLM (via MCP) ---")
    print(prompt)
    print("--------------------------------------")
    return "Baseado nos dados recuperados: " + context

if __name__ == "__main__":
    # 1. Usuário faz uma pergunta e a LLM converte para embedding
    user_query = "Houve algum problema com veículos na pista hoje?"
    # Simulação do embedding da pergunta gerado pela IA
    query_emb = np.array([0.15, 0.85, 0.25]) 

    print("Buscando no Vector Database...")
    # 2. Retrieval: busca contexto similar
    top_docs = retrieve_context(query_emb)
    
    if top_docs:
        best_score, best_doc = top_docs[0]
        context_text = best_doc["text"]
        
        # 3. Generation: Augment prompt e gera
        final_answer = generate_response(user_query, context_text)
        print("\n[Assistente]:", final_answer)
