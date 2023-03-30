import os
import openai
"""
    Kaiza Studios gpt3 class
    you need to set up your environment strings, see os.getenv below
    OPENAI_API_KEY is issued by OpenAi 
    OPENAI_ORG is the key string OpenAi issued for your organization

"""
class GPT3(object):
    def __init__(self, openai_api_key:str = "", openai_org_key:str = "", openai_model:str = "text-ada-001"):
        if (len(openai_api_key) > 0):
             self.envKey = openai_api_key
        else:
            self.envKey = os.getenv("OPENAI_API_KEY")
        if (len(openai_org_key) > 0):
             self.orgKey = openai_org_key
        else:
            self.orgKey = os.getenv("OPENAI_ORG")
        openai.organization = self.orgKey
        openai.api_key = self.envKey
        self.lastQuery = ""
        self.lastResponse = ""
        self.openAIResponse = None
        self.max_tokens = 2048
        self.setModel(openai_model)

    def setModel(self, openai_model:str = "text-ada-001"):
        if (openai_model != ""):
            self.model = openai_model
        if (self.model == "text-davinci-003"):
            self.max_tokens = 3600 
        elif (self.model == "text-curie-001"):
            self.max_tokens = 1600
        elif (self.model == "text-babbage-001"):
            self.max_tokens = 1600
        elif (self.model == "text-ada-001"):
            self.max_tokens = 600
        elif (self.model == "gpt-3.5-turbo"):
            self.max_tokens = 4000
        else:
            # let's assume there is a new model
            self.model = openai_model
            self.max_tokens = 600

    def setGPT35(self):
        self.model = f"gpt-3.5-turbo"
        self.max_tokens = 3600          

    def setDavinci(self, level:int = 3):
        self.model = f"text-davinci-{level:03d}"
        self.max_tokens = 3600

    def setCurie1(self):
        self.model = "text-curie-001"
        self.max_tokens = 1600

    def setBabbage1(self):
        self.model = "text-babbage-001"
        self.max_tokens = 1600   

    def setAda1(self):
        self.model = "text-ada-001"
        self.max_tokens = 1600

    def getModel(self):
        return self.model
    
    def checkQuery(self, query:str) -> bool:
        return len(query) > 0
    
    def getLastQuery(self) -> str:
        return self.lastQuery
    
    def getLastResponse(self) -> str:
         return self.lastResponse
    
    def getLastOpenAiResponse(self) -> object:
         return self.getLastOpenAiResponse
    
    def explainCompletion(self):
        print(f' Completion Mode.\n')
        print(f' Model will return one or more responses to your question.\n')
        print(f' Example: "What should I do today?"\n')    
 
    def doCompletion(self, query:str = 'What should I do today?') -> bool:
        result = False
        try:
            if (self.checkQuery(query)):
                self.lastQuery = query
                self.lastOpenAiResponse = openai.Completion.create(
                    model = self.model,
                    prompt = query,
                    temperature = 0.5,
                    max_tokens = self.max_tokens,
                    top_p = 0.3,
                    frequency_penalty = 0.5,
                    presence_penalty = 0)
                self.lastResponse = self.lastOpenAiResponse['choices'][0].text
                result = True                
        except:
            print(f'Not all is well in completion Mudville!')
        return result

    def endOfGpt3(self):
         pass
"""
    end of GPT3 class
"""
def getQuery(prompt:str = "What's your question") -> str:
    return input(f" {prompt}? ->")

def getCompletionResponse(model:str = 'ada', query:str = 'How are you?', g:GPT3 = None) -> str:
    if (g == None):
        raise Exception("you need to pass an instance of class GPT3 as the g parameter")
    model = model.lower()
    if ('ada' in model):
        g.setAda1()
    elif ('babbage' in model):
        g.setBabbage1()
    elif ('curie' in model):
        g.setCurie1()
    elif ('davinci' in model):
        g.setDavinci()
    else:
        g.setModel(model)
    g.doCompletion(query)
    return g.getLastResponse()

def main():
    gpt3 = GPT3()
    while (True):
        try:
            print(f'\n\n Modes: \n 1. Chat\n 2. Image\n 3. Completion\n 4. Audio\n 5. Embedding\n 6. Edits\n')
            mode = input(f'\nInput the number of your desired mode of interaction with the Model: --> ')
            if (mode == ""):
                break
            mode = int(mode)
            if (mode <= 0 or mode > 7):
                raise Exception(f' Plese select a mode between 1 and 6')
            elif (mode == 1):
                print(f' Chat')
            elif (mode == 2):
                print(f' Image')     
            if (mode == 3):
                print(f' Completion')
                gpt3.explainCompletion()
                query = getQuery("What's your question? Should be ambiguous.")
                adaResponse = getCompletionResponse('ada', query, gpt3)
                print(f"text-ada-001''s response: {adaResponse}")
                babbageResponse = getCompletionResponse('babbage', query, gpt3)
                print(f'babbage response: {babbageResponse}')
                curieResponse = getCompletionResponse('curie', query, gpt3)
                print(f'curie response: {curieResponse}')
                davinciResponse = getCompletionResponse('davinci', query, gpt3)
                print(f'davinci-003 response: {davinciResponse}')
                gpt35Response = getCompletionResponse('gpt-3.5-turbo', query, gpt3)
                print(f'gpt35turbo response: {gpt35Response}')
            elif (mode == 4):
                print(f' Audio')
            elif (mode == 5):
                print(f'Chat')
            else:
                break
        except Exception as e:
            print(f'\n\n FAT FINGERS! {repr(e)} {vars(e)}\n')
            break

if __name__ == "__main__":
     main()
         

