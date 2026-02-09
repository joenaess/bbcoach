import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Local Model Fallback
LOCAL_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"


class BasketballCoach:
    def __init__(self, provider="local", api_key=None, model_name=None):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.model = None
        self.client = None

        print(
            f"Initializing Coach with provider: {self.provider}, model: {self.model_name}"
        )

        self._setup_provider()

    def _setup_provider(self):
        try:
            if self.provider == "gemini":
                import google.generativeai as genai

                if not self.api_key:
                    raise ValueError("Gemini API Key required")
                genai.configure(api_key=self.api_key)
                # Use provided model or default
                m = self.model_name if self.model_name else "gemini-2.0-flash"
                self.model = genai.GenerativeModel(m)

            elif self.provider == "openai":
                from openai import OpenAI

                if not self.api_key:
                    raise ValueError("OpenAI API Key required")
                self.client = OpenAI(api_key=self.api_key)

            elif self.provider == "anthropic":
                from anthropic import Anthropic

                if not self.api_key:
                    raise ValueError("Anthropic API Key required")
                self.client = Anthropic(api_key=self.api_key)

            else:  # local
                self.provider = "local"  # Enforce local if others fail
                self._setup_local()

        except Exception as e:
            print(f"Error initializing {self.provider}: {e}. Falling back to Local.")
            self.provider = "local"
            self._setup_local()

    def _setup_local(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading local model {LOCAL_MODEL_NAME} on {device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(
            LOCAL_MODEL_NAME,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
        )
        if device != "cuda":
            self.model.to(device)

        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )

    def ask(self, context: str, question: str) -> str:
        full_prompt = f"{context}\n\nUser Question: {question}\nAssistant Coach:"

        try:
            if self.provider == "gemini":
                response = self.model.generate_content(full_prompt)
                return response.text

            elif self.provider == "openai":
                m = self.model_name if self.model_name else "gpt-4o"
                response = self.client.chat.completions.create(
                    model=m,
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": question},
                    ],
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                m = self.model_name if self.model_name else "claude-3-5-sonnet-latest"
                response = self.client.messages.create(
                    model=m,
                    max_tokens=1000,
                    system=context,
                    messages=[{"role": "user", "content": question}],
                )
                return response.content[0].text

            else:  # Local
                # Format for ChatML (Qwen)
                messages = [
                    {"role": "system", "content": context},
                    {"role": "user", "content": question},
                ]
                prompt = self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                outputs = self.pipe(
                    prompt,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7,
                    top_k=50,
                    top_p=0.95,
                )
                response = outputs[0]["generated_text"]
                if "<|im_start|>assistant" in response:
                    response = response.split("<|im_start|>assistant")[-1].strip()
                return response

        except Exception as e:
            return f"Error executing AI request ({self.provider}): {str(e)}"

    def get_model_info(self) -> str:
        icons = {
            "gemini": "Googe Gemini 2.0 Flash ⚡",
            "openai": "OpenAI GPT-4o 🧠",
            "anthropic": "Claude 3.5 Sonnet 🎭",
            "local": f"Local Model ({LOCAL_MODEL_NAME}) 💻",
        }
        return icons.get(self.provider, "Unknown Model")


if __name__ == "__main__":
    coach = BasketballCoach()
    print(coach.ask("Player A averages 20ppg.", "Is Player A a good scorer?"))
