from app import pc


class PineconeService:
    def __init__(self) -> None:
        self.index = pc.Index(host="PINECONE_HOST")

    def insert_items(self, data_chunks, agent_id):
        #Генеруэмо список текстыв з масиву data chunks
        data = [data_chunk.text for data_chunk in data_chunks]

        #Виконуємо обчислення ембедингів для списку текстів із використанням моделі "multilingual-e5-large". 
        # Параметри: 
        # "input_type": "passage" - вказує, що вхідними даними є фрагменти тексту (passages), 
        # "truncate": "END" - при необхідності текст буде вкорочено з кінця.

        embeddings = pc.inference.embed(
            model='multilingual-e5-large',
            inputs=data,
            parameters={
                "input_type": "passage",
                "truncate": "END"
            }
        )

        vectors = []
        # Для кожного data_chunk та відповідного ембедингу 
        # формуємо словник з id, ембедингами 
        # та метаданими, що включають текст та content_item_id.

        for data_chunk, embedding in zip(data_chunks, embeddings):
            vectors.append({
                "id": f"{data_chunk.id}",
                "values": embedding['values'],
                "metadata": {
                    "text": data_chunk.text,
                    "content_item_id": data_chunk.content_item_id
                }
            })
        
        # Додаємо вектори доіндексу. 
        # namespace=f"{agent_id}" дає змогу організувати дані за певним ідентифікатором, в нашому випадку agent_id.

        self.index.upsert(
            vectors=vectors,
            namespace=f"{agent_id}"
        )
    
    def query(self, query_string, agent_id, limit):
        # Спершу отримуємо ембединг для запиту (query_string) за допомогою моделі "multilingual-e5-large".
        embedding = pc.inference.embed(
            model='multilingual-e5-large',
            inputs=[query_string],
            parameters={"input_type": "query"}
        )

        # Виконуємо пошук за допомогою векторного індексу. 
        # Передаємо такі параметри: 
        # namespace=f"{agent_id}" - визначаємо, в якому namespace шукати. 
        # vector=embedding[0].values - використовуємо обчислений ембединг як вектор для пошуку. 
        # top_k=limit - кількість найбільш релевантних результатів, які необхідно повернути.
        # include_values=False - оскільки нам не потрібні безпосередньо вектори результатів, ми їх не включаємо. 
        # include_metadata=True - ми хочемо отримати метадані, в яких міститься потрібний текст.

        result = self.index.query(
            namespace=f"{agent_id}",
            vector=embedding[0].values,
            top_k=limit,
            include_values=False,
            include_metadata=True
        )

        # Повертаємо масив текстів з метаданих усіх відповідних результатів.
        return [item["metadata"]["text"] for item in result['matches']]
    
    def delete_namespace(self, agent_id):
        self.index.delete(delete=True, namespace=f"{agent_id}")
    
    def delete_content_item(self, ids, agent_id):
        self.index.delete(
            ids=ids,
            namespace=f"{agent_id}"
        )