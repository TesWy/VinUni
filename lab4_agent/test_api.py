import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

load_dotenv()

PROMPT = "Xin chao?"


def test_openai() -> None:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Thieu OPENAI_API_KEY, bo qua OpenAI.")
        return

    llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
    print("OpenAI:")
    print(llm.invoke(PROMPT).content)


def test_gemma() -> None:
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        print("Thieu GOOGLE_API_KEY hoac GEMINI_API_KEY, bo qua Gemma.")
        return

    llm = ChatGoogleGenerativeAI(
        model="gemma-4-31b-it",
        google_api_key=google_api_key,
    )
    print("Gemma:")
    print(llm.invoke(PROMPT).content)


if __name__ == "__main__":
    test_openai()
    print("-" * 40)
    test_gemma()
