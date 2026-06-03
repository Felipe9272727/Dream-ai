"""
👨‍💻 O modelo Coder — o cérebro de programação do Dream-AI.

Carrega um modelo base aberto de ~1B parâmetros, especializado em código, e o usa para
gerar soluções. Recomendado: Qwen2.5-Coder-1.5B-Instruct (o melhor modelo de código
pequeno disponível hoje, junho/2026), mas é configurável.

Honestidade: este arquivo PRECISA da biblioteca `transformers` e de uma GPU (Colab Pro)
para rodar de verdade. Em CPU sem o modelo, ele só funciona em modo "mock" para testes.
"""

from __future__ import annotations

import os
import re

# Modelo base padrão. Alternativas boas de ~1B para código:
#   - "Qwen/Qwen2.5-Coder-1.5B-Instruct"  (recomendado)
#   - "Qwen/Qwen2.5-Coder-0.5B-Instruct"  (mais leve)
#   - "deepseek-ai/deepseek-coder-1.3b-instruct"
DEFAULT_BASE_MODEL = os.environ.get(
    "DREAM_BASE_MODEL", "Qwen/Qwen2.5-Coder-1.5B-Instruct"
)


def extract_code(text: str) -> str:
    """Extrai o bloco de código de uma resposta do modelo (remove markdown ```)."""
    fences = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
    if fences:
        return fences[0].strip()
    return text.strip()


class CoderModel:
    """Wrapper sobre um modelo HF de código. Carrega sob demanda."""

    def __init__(
        self,
        base_model: str = DEFAULT_BASE_MODEL,
        adapter_path: str | None = None,
        load_in_4bit: bool = True,
        device: str | None = None,
    ):
        self.base_model = base_model
        self.adapter_path = adapter_path
        self.load_in_4bit = load_in_4bit
        self.device = device
        self.model = None
        self.tokenizer = None

    def load(self) -> None:
        """Carrega o modelo e o tokenizer (e o adapter LoRA, se houver)."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")

        quant_args = {}
        if self.load_in_4bit and device == "cuda":
            from transformers import BitsAndBytesConfig

            quant_args["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )

        print(f"📥 Carregando modelo base: {self.base_model} (4bit={self.load_in_4bit})")
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto" if device == "cuda" else None,
            **quant_args,
        )

        if self.adapter_path and os.path.exists(self.adapter_path):
            from peft import PeftModel

            print(f"🧩 Aplicando adapter LoRA: {self.adapter_path}")
            self.model = PeftModel.from_pretrained(self.model, self.adapter_path)

        self.model.eval()
        print("✅ Modelo coder pronto.")

    def solve(
        self,
        instruction: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        self_description: str | None = None,
    ) -> str:
        """Gera uma solução de código para uma instrução.

        Se `self_description` for passado (a autoconsciência da IA sobre seu estado
        interno), ele é injetado no system prompt para o modelo se entender melhor.
        """
        if self.model is None:
            raise RuntimeError("Modelo não carregado. Chame .load() primeiro.")

        import torch

        system = (
            "Você é um programador expert. Escreva código Python correto e limpo. "
            "Se não souber resolver, diga honestamente em vez de inventar."
        )
        if self_description:
            system = self_description + "\n\n" + system

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": instruction},
        ]
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        gen = out[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(gen, skip_special_tokens=True)
