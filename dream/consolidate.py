"""
😴 Consolidação — a fase de sono profundo.

Aqui acontece a "consolidação de memória": pegamos as soluções que foram SONHADAS e
VERIFICADAS (passaram na execução real) e fazemos um fine-tuning leve (LoRA) do modelo
nelas. É assim que o aprendizado do sonho vira conhecimento permanente.

Análogo biológico: durante o sono profundo, o cérebro reativa e consolida o que foi
aprendido no dia. Análogo em IA: STaR / self-training com filtragem por verificação.

Precisa de `peft`, `transformers`, `datasets` e GPU (Colab Pro).
"""

from __future__ import annotations

import json
import os

# Cada item da memória do sonho: instrução + solução verificada.
# Salvamos em JSONL para ser auditável (honestidade: dá pra inspecionar o que ele aprendeu).
DREAM_MEMORY_PATH = "dream_memory/verified.jsonl"


def remember(instruction: str, solution_code: str, score: float) -> None:
    """Grava uma solução verificada na memória de sonhos (JSONL auditável)."""
    os.makedirs(os.path.dirname(DREAM_MEMORY_PATH), exist_ok=True)
    with open(DREAM_MEMORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "instruction": instruction,
            "solution": solution_code,
            "score": score,
        }, ensure_ascii=False) + "\n")


def load_memory() -> list[dict]:
    if not os.path.exists(DREAM_MEMORY_PATH):
        return []
    with open(DREAM_MEMORY_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def consolidate(
    coder,
    output_dir: str = "adapters/dream_lora",
    epochs: int = 1,
    lr: float = 2e-4,
    min_examples: int = 8,
) -> str | None:
    """
    Faz fine-tuning LoRA do modelo nas soluções verificadas.

    Retorna o caminho do adapter salvo, ou None se não houver memória suficiente.
    """
    memory = load_memory()
    if len(memory) < min_examples:
        print(f"💤 Memória insuficiente para consolidar "
              f"({len(memory)}/{min_examples}). Continue sonhando.")
        return None

    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling

    tokenizer = coder.tokenizer
    model = coder.model

    # Monta exemplos no formato de chat
    def to_text(ex):
        messages = [
            {"role": "system", "content": "Você é um programador expert e honesto."},
            {"role": "user", "content": ex["instruction"]},
            {"role": "assistant", "content": "```python\n" + ex["solution"] + "\n```"},
        ]
        return tokenizer.apply_chat_template(messages, tokenize=False)

    texts = [to_text(ex) for ex in memory]
    ds = Dataset.from_dict({"text": texts})

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=1024)

    ds = ds.map(tokenize, batched=True, remove_columns=["text"])

    # Configura LoRA (treina poucos parâmetros — viável no Colab)
    lora = LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        num_train_epochs=epochs,
        learning_rate=lr,
        logging_steps=5,
        save_strategy="no",
        bf16=torch.cuda.is_available(),
        report_to=[],
    )
    collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)
    trainer = Trainer(model=model, args=args, train_dataset=ds, data_collator=collator)

    print(f"😴 Consolidando {len(memory)} memórias de sonho via LoRA ...")
    trainer.train()

    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    print(f"🧠 Adapter consolidado salvo em {output_dir}")
    return output_dir
