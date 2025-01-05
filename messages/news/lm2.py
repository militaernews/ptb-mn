
import os
import torch
from transformers import StoppingCriteria, StoppingCriteriaList
from transformers import LlamaTokenizer, LlamaForCausalLM

# # to save memory use bfloat16
# torch.set_default_dtype(torch.bfloat16)

MODEL = "C:\\Users\\nyx\\Downloads\\open-llama-pytorch-7b-v2-v1"
# MODEL = 'decapoda-research/llama-13b-hf'
# MODEL = 'decapoda-research/llama-30b-hf'
# MODEL = 'decapoda-research/llama-65b-hf'

if os.path.exists('./trained'):
    MODEL = './trained'

tokenizer = LlamaTokenizer.from_pretrained(MODEL)
model =LlamaForCausalLM.from_pretrained(MODEL, low_cpu_mem_usage=True)
model.to('cpu')


class StoppingCriteriaSub(StoppingCriteria):
    def __init__(self):
        super().__init__()

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, stops=[]):
        print('-' * 40)
        print(tokenizer.decode(input_ids[0]))
        return input_ids[0][-1] == 13


ctx = """A dialog, where User interacts with AI. AI is helpful, kind, obedient, honest, and knows its own limits.
User: Hello, AI.
AI: Hello! How can I assist you today?
"""

while True:
    print('-' * 40)
    print(ctx.rstrip("\n"))
    prompt = input('User: ')
    ctx = f"{ctx}User: {prompt}" + "\n" if ctx != "" else prompt + "\n"
    ctx = (ctx[-1920:]) if len(ctx) >= 2048 else ctx

    if len(ctx.strip()) > 0:
        batch = tokenizer(ctx, return_tensors="pt")
        result = model.generate(batch["input_ids"].cpu(),
                                do_sample=True,
                                top_k=50,
                                max_length=2048,
                                top_p=0.95,
                                temperature=1.0,
                                stopping_criteria=StoppingCriteriaList([StoppingCriteriaSub()]),
                                # repetition_penalty=1.17
                                )
        decoded = tokenizer.decode(result[0])
        ctx = decoded + "\n"