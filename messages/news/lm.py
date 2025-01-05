import torch
import transformers
import sentencepiece
import accelerate
#import protobuf
import safetensors
from transformers import LlamaTokenizer, LlamaForCausalLM

model = "C:\\Users\\nyx\\Downloads\\open-llama-pytorch-7b-v2-v1"
prompt = "Q: What is the approximate number of luffas that a fully grown luffa tree can produce in a single growing season?\nA:"
offload ='C:\\Users\\nyx\\Downloads\\offload'

tokenizer = LlamaTokenizer.from_pretrained(model) #,legacy=False
model = LlamaForCausalLM.from_pretrained(
    model, torch_dtype=torch.float16, device_map='auto', use_safetensors=True, offload_folder=offload
)
print(prompt)

prompt = prompt
input_ids = tokenizer(prompt, return_tensors="pt").input_ids

generation_output = model.generate(
    input_ids=input_ids, max_new_tokens=32
)

print(generation_output)

text =tokenizer.decode(generation_output[0], skip_special_tokens=True)

print(text)