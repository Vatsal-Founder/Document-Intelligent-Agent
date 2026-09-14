from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI



agentmodel =  ChatOpenAI(model='gpt-4o-mini')

policy_model = ChatOpenAI(model='gpt-4o-mini')


supervisor_model= ChatOpenAI(model="gpt-4o-mini")

financial_model=ChatOpenAI(model="gpt-4o-mini")

grader_model=ChatOpenAI(model="gpt-4o-mini",temperature=0)