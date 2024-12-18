import ollama

class OllamaService:
    def __init__(self):
        self.client = ollama.Client(host='http://localhost:11434')
        
    def get_answer(self, message, data):
        
        formatted_data = '\n'.join([f"<chunk>\n{chunk}\n</chunk>" for chunk in data])

        content = f"""Answer the question: {message}\n
        Using next data: \n{formatted_data}
        Provide answer only for asked question, do not add any additional information.
        Provide as much information as possible, but do not provide any information that is not asked for.
        """
        print(f'Content: {content}')
        response = self.client.chat(model='llama3.2:1b',
                                    messages=[
                                        {
                                            "role": "system",
                                            "content": "You are a helpful assistant. Precisely follow the instructions provided in the chat. If you can't find the answer in the provided data, answer with 'I don't know'."
                                        },
                                        {
                                            "role": "user",
                                            "content": content
                                        }
                                    ],
                                    options={
                                        "max_tokens": 5000,
                                        "temperature": 0.7,
                                        "top_p": 0.9,
                                        "frequency_penalty": 0.0,
                                        "presence_penalty": 0.0,
                                    }
                                    )
        
        return response['message']['content']        
       
    def get_embedding(self, text):
        response = self.client.embed(model='llama3.2:1b', input=text)
        embedding = response['embeddings'][0]
        return embedding

    def generate_chunk_context(self, chunk, document_content):
        prompt = f"""
        <document>
        {document_content}
        </document>

        Here is the chunk we want to situate within the whole document
        <chunk>
        {chunk}
        </chunk>

        Please give a short succinct context to situate this chunk within the overal document for the purposes of improving search retrieval of the chunk.
        Answer only with the succinct context and nothing else.
        """

        response = self.client.chat(model='llama3.2:1b',
                                    messages=[
                                        {
                                            "role": "user",
                                            "content": prompt
                                        }
                                    ])
        
        return response['message']['content']
        
    def generate_document_summary(self, document):
        prompt = f"""
        <document>
        {document}
        </document>

        Craft a summary of the document that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness. Incorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects. Rely strictly on the provided text, without including external information. Format the summary in paragraph form for easy understanding.
        """

        response = self.client.chat(model='llama3.2:1b',
                                    messages=[
                                        {
                                            "role": "user",
                                            "content": prompt
                                        }
                                    ])
        return response['message']['content']