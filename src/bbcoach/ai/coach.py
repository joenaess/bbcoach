import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Check for Gemini Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    print("Gemini API Key found. Using Google Gemini Flash.")
else:
    print("No Gemini API Key found. Using Local LLM.")
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Model ID for Local Fallback
LOCAL_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"


class BasketballCoach:
    def __init__(self, device=None):
        self.use_gemini = bool(GEMINI_API_KEY)

        if self.use_gemini:
            import google.generativeai as genai

            # device is not really used for API, but keep for compat
            self.device = "cpu"
            self.model = genai.GenerativeModel("gemini-2.0-flash")
            print("Gemini 2.0 Flash loaded.")
        else:
            import torch

            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
            self.device = device

            print(f"Loading local model {LOCAL_MODEL_NAME} on {self.device}...")
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
            print("Local Model loaded.")

    def ask(self, context: str, question: str) -> str:
        if self.use_gemini:
            # Gemini Call
            prompt = f"""
            SYSTEM: You are a professional basketball coach for the Swedish Basketball League.
            CONTEXT:
            {context}
            
            USER QUESTION: {question}
            """
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                return f"Error calling Gemini API: {e}"
        else:
            # Local LLM Call
            messages = [
                {
                    "role": "system",
                    "content": "You are a professional basketball coach for the Swedish Basketball League. You analyze stats and provide insights.",
                },
                {
                    "role": "user",
                    "content": f"Context Stats:\n{context}\n\nQuestion: {question}",
                },
            ]

            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            outputs = self.pipe(
                prompt,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
            )
            generated_text = outputs[0]["generated_text"]

            # Extract response
            response = (
                generated_text.split(prompt)[-1]
                if prompt in generated_text
                else generated_text
            )

            # Clean up Qwen specific artifacts if any
            if "<|im_start|>assistant" in response:
                response = response.split("<|im_start|>assistant")[-1].strip()

        return response.strip()

    def get_model_info(self) -> str:
        """Returns the name of the currently active model."""
        if self.use_gemini:
            return "Google Gemini 1.5 Flash ⚡"
        else:
            return f"Local Model ({LOCAL_MODEL_NAME}) 💻"


if __name__ == "__main__":
    coach = BasketballCoach()
    print(coach.ask("Player A averages 20ppg.", "Is Player A a good scorer?"))
