import os
import openai

envKey = os.getenv("OPENAI_API_KEY")
orgKey = os.getenv("OPENAI_ORG")
organization = 'KaizaStudios'
openai.organization = orgKey
openai.api_key = envKey
openai.Model.list()

while (True):
    query = input("What's your question? -> ")
    if (query == ""):
        break
    response = openai.Completion.create(
        model = "text-davinci-003",
        prompt = query,
        temperature = 0.5,
        max_tokens = 600,
        top_p = 0.3,
        frequency_penalty = 0.5,
        presence_penalty = 0)
    print(repr(response))
    print(response['choices'][0].text)
