import gc
from functools import cached_property

import json
import torch

from transformers import (AutoTokenizer, AutoModelForCausalLM, AutoProcessor, BitsAndBytesConfig,
                          Qwen2_5_VLForConditionalGeneration)

from chonkie import SemanticChunker, Model2VecEmbeddings
from sentence_transformers import SentenceTransformer, CrossEncoder
from qwen_vl_utils import process_vision_info

class CleanupMixin:
    def cleanup_cuda(self):
        """Fully clears GPU memory."""
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        torch.cuda.synchronize()
        gc.collect()

    def cleanup_model(self, model):
        """Moves model to CPU, deletes it, and clears CUDA."""
        if model is not None:
            try:
                model.to("cpu")
            except Exception:
                pass
            del model
        gc.collect()
        self.cleanup_cuda()


class Embeddings(CleanupMixin):
    def __init__(self, cache_dir, model_name, model_kwargs=None,
                 processor_kwargs=None, quantization_kwargs=None,
                 prompt= None,
                 device="cuda"):
        """
        creates embeddings from text and images, this is using a vision language embedder
        :param cache_dir: where the models are
        :param model_name: name of the model
        :param model_kwargs: kwargs to pass to the model
        :param processor_kwargs: kwargs to pass to the processor
        :param quantization_kwargs: quantization if you are using bitsandbytes
        :param prompt: the prompt for the model
        :param device: which device to use defaults to cuda
        """
        self.cache_dir = cache_dir
        self.model_name = model_name
        self.model_kwargs = model_kwargs if model_kwargs is not None else {}
        if quantization_kwargs is not None:
            quantization=BitsAndBytesConfig(**quantization_kwargs)
            self.model_kwargs["quantization_config"]=quantization
        if processor_kwargs is not None:
            self.model_kwargs["processor_kwargs"]=processor_kwargs
        self.device = device
        self.prompt = prompt

    @cached_property
    def model(self):
        """
        load the model with kwargs
        :return: a transformsers model
        """
        self.model_kwargs["torch_dtype"]=torch.bfloat16
        model=SentenceTransformer(self.model_name, cache_folder=self.cache_dir,
                                  model_kwargs=self.model_kwargs)
        return model

    def encode(self, items):
        """
        encode items into embeddings, these can be images or texts or a pair of both
        :param items: this is a list of dict, and it HAS TO look like this
        [{"type":"text", "text":<the actual text>}, # text only
        {"type": "image", "image":<actual image>}, # image only
        {"type: "image", "image": <actual image>, "type": "text", "text":<actual text>}] #image text combo
        :return: embeddings dim 4096
        """
        embeddings = self.model.encode(items, prompt=self.prompt, device=self.device)
        return embeddings

    def cleanup(self, model=False):
        """Calls the cleanup mixin"""
        self.cleanup_cuda()
        if model:
            self.cleanup_model(self.model)


class ReRank(CleanupMixin):
    def __init__(self, cache_dir, model_name, model_kwargs=None,
                 processor_kwargs=None, quantization_kwargs=None,
                 prompt=None,
                 device="cuda"):
        """
        Reranker for images AND text, same idea as the embeddings
        :param cache_dir: where the models are
        :param model_name: name of the model
        :param model_kwargs: kwargs to pass to the model
        :param processor_kwargs: kwargs to pass to the processor
        :param quantization_kwargs: quantization kwargs
        :param prompt: prompt for the model
        :param device: device to use defaults to cuda
        """
        self.cache_dir = cache_dir
        self.model_name = model_name
        self.model_kwargs = model_kwargs if model_kwargs is not None else {}
        if quantization_kwargs is not None:
            quantization = BitsAndBytesConfig(**quantization_kwargs)
            self.model_kwargs["quantization_config"] = quantization
        if processor_kwargs is not None:
            self.model_kwargs["processor_kwargs"] = processor_kwargs
        self.device = device
        self.prompt = prompt

    @cached_property
    def model(self):
        """Load the model"""
        self.model_kwargs["torch_dtype"] = torch.bfloat16
        model=CrossEncoder(self.model_name, cache_folder=self.cache_dir, model_kwargs=self.model_kwargs,
        device=self.device)

        return model

    def rerank(self, query, items):
        """
         encode items into embeddings, these can be images or texts or a pair of both
         :param items: this is a list of dict, and it HAS TO look like this
         [{"type":"text", "text":<the actual text>}, # text only
         {"type": "image", "image":<actual image>}, # image only
         {"type: "image", "image": <actual image>, "type": "text", "text":<actual text>}] #image text combo
         :return: ranking score
         """
        scores=self.model.rank(query, items, self.prompt)
        return scores

    def cleanup(self, model=False):
        self.cleanup_cuda()
        if model:
            self.cleanup_model(self.model)


class SemanticChunk(CleanupMixin):
    def __init__(self, chunking_model, chunk_size=100, min_sentences=1,
                 threshold=0.8):
        """
        :param chunking_model: chunking model it can be anything really but we are using a static model for speed
        :param chunk_size: how many tokens approx a chunk should have
        :param min_sentences: how many sentences a chunk should have at the minimum. It did not makes sense to me to split sentences so we are
        sticking with 1
        :param threshold: when to start a new chunk, this is based on the delta for the embedding cosines.
        """
        self.chunking_model = Model2VecEmbeddings(chunking_model)
        self.chunk_size=chunk_size
        self.min_sentences=min_sentences
        self.threshold=threshold

    def chunk_text(self, texts):
        """Chunk notes into semantic segments. this will return a list of strings, i will then use an embedding model"""
        chunker = SemanticChunker(
            embedding_model=self.chunking_model,
            threshold=self.threshold,  # Similarity threshold (0-1) or (1-100) or "auto"
            chunk_size=self.chunk_size,  # Maximum tokens per chunk
            min_sentences=self.min_sentences,  # Initial sentences per chunk,
            return_type="texts"  # return a list of strings
        )
        if not isinstance(texts, list):
            texts=[texts]

        chunked_texts = []
        for text in texts:
            chunked=chunker.chunk(text)
            for index, chunk in enumerate(chunked):
                chunked_texts.append((index, chunk.text))

        return chunked_texts


class InterpretImage(CleanupMixin):
    def __init__(self, cache_dir, model_name, model_kwargs, processor_kwargs, quantization_kwargs,
                 model_class=Qwen2_5_VLForConditionalGeneration,
                 processor_class=AutoProcessor, device="cuda"):
        """
        Runs a vision language models to generate captions for an image, this is primarily used for figure and
        table captioninig
        :param cache_dir: where the models are
        :param model_name: name of the model
        :param model_kwargs: kwargs to pass to the model
        :param processor_kwargs:kwargs to pass to the processor
        :param quantization_kwargs:quantization kwargs
        :param model_class:model class (use this if you are not using basic AutoModel)
        :param processor_class: what kind of processor to use, defaults to AutoProcessor
        :param device: device to use defaults to cuda
        """
        self.cache_dir = cache_dir
        self.model_name = model_name
        self.model_class=  model_class
        self.model_kwargs=model_kwargs
        if quantization_kwargs is not None:
            self.quantization = BitsAndBytesConfig(**quantization_kwargs)
        else:
            self.quantization=None
        self.processor_class=processor_class
        self.processor_kwargs=processor_kwargs
        self.device = device

    @cached_property
    def model(self):
        """Load the model with kwargs"""
        self.model_kwargs["torch_dtype"] = torch.bfloat16
        if self.quantization is not None:
            model=self.model_class.from_pretrained(self.model_name, cache_dir=self.cache_dir, **self.model_kwargs,
                                               quantization_config=self.quantization,)
        else:
            model = self.model_class.from_pretrained(self.model_name, cache_dir=self.cache_dir, **self.model_kwargs)
        return model

    @cached_property
    def processor(self):
        """Load the processor with kwargs"""
        processor=self.processor_class.from_pretrained(self.model_name, cache_dir=self.cache_dir, **self.processor_kwargs)
        return processor

    @torch.inference_mode
    def interpret(self, sys_prompt, images):
        """
        run inference on an image
        :param sys_prompt: system prompt
        :param images: list of images to process
        :return: captions for the images based on the prompt
        """
        outputs=[]
        for image in images:
            messages = [{"role": "system", "content": [{"type": "text",
                                                        "text": sys_prompt}]},
                        {"role": "user", "content": [{"type": "image", "image": image, }], }]


            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            #TODO this actually breaks the flexibility, I will need to adress this later
            # this is here for compatibility I will not be processing videos
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to(self.device)
            generated_ids = self.model.generate(**inputs, max_new_tokens=self.config["vl_model"]["model"]["max_tokens"])
            generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids,
            out_ids in zip(inputs.input_ids, generated_ids)]
            output_text = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            outputs.append(output_text)
        return outputs

    def cleanup(self, model=False):
        self.cleanup_cuda()
        if model:
            self.cleanup_model(self.model)

class ExtractInfo(CleanupMixin):
    def __init__(
        self,
        cache_dir,
        model_name,
        model_kwargs=None,
        tokenizer_kwargs=None,
        quantization_kwargs=None,
        generation_kwargs=None,
        model_class=AutoModelForCausalLM,
        device="cuda",
    ):
        """
        Extract information from an a piece of text, the idea is to use this to return structured information from
        unstructured text like abstracts or paper text
        :param cache_dir: where the models are
        :param model_name: name of the model
        :param model_kwargs: kwargs to pass to the model
        :param tokenizer_kwargs: kwargs to pass to the tokenizer
        :param quantization_kwargs: quantization kwargs
        :param generation_kwargs: generation kwargs like temperature max tokens etc
        :param model_class: What kind of model to use, the default is AutoModelForCausalLM
        :param device: device to use defaults to cuda
        """
        self.cache_dir = cache_dir
        self.model_name = model_name
        self.model_class = model_class
        self.device = device

        # defensive copies (avoid external mutation bugs)
        self.model_kwargs = dict(model_kwargs or {})
        self.tokenizer_kwargs = dict(tokenizer_kwargs or {})
        self.generation_kwargs = dict(generation_kwargs or {})
        self.quantization_kwargs = dict(quantization_kwargs or {})

    @cached_property
    def model(self):
        "Load the model with kwargs"
        self.model_kwargs["torch_dtype"] = torch.bfloat16
        if self.quantization_kwargs:
            quantization_config = BitsAndBytesConfig(**self.quantization_kwargs)
            # set attribute correctly (not dict-style)
            quantization_config.bnb_4bit_compute_dtype = torch.bfloat16
        else:
            quantization_config = None

        model = self.model_class.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            quantization_config=quantization_config,
            **self.model_kwargs,
        )

        # only move manually if NOT quantized
        if quantization_config is None:
            model = model.to(self.device)

        return model

    @cached_property
    def tokenizer(self):
        "load the tokenizer"
        tokenizer=AutoTokenizer.from_pretrained(self.model_name, self.cache_dir,
                                                **self.tokenizer_kwargs)
        return tokenizer

    def _generate_extraction_prompt(self, items_to_extract: dict):
        """
        generate extraction prompt based on what to return the items to extract is a dict of what you want to extract
        and a description of what it looks like
        :param items_to_extract: dict
        :return: a processed prompt
        """
        description_text = []
        format_text = []

        for item, description in items_to_extract.items():
            description_text.append(f"- {item}: {description}\n")
            format_text.append(
                f'{item}: [comma(,) separated list of each member of {item}],\n'
            )

        prompt = f"""
For each of the texts that are provided extract the following information:

{''.join(description_text)}

For each of the items mentioned above your response should come in the following schema:
{{
{''.join(format_text)}
}}

Rules:
- Do not invent or modify what you are looking for
- Not every possible item will be in each text
- There might be more than one item in each text include all of them
- Always return json, no markdown, no comments, no additional formatting
- If there is no information relating to a specific field return empty list and nothing else

Text:
"""
        return prompt

    @torch.inference_mode()
    def extract_info(self, sys_prompt, items_to_extract: dict, texts: list):
        """
        use the extracted prompt from above to call the model
        :param sys_prompt: system prompt with instructions
        :param items_to_extract: the dict of what to extract
        :param texts: the text to extract things from
        :return: hopefully a json file
        """
        prompt = self._generate_extraction_prompt(items_to_extract)
        results = []

        for text in texts:
            if text is None:
                results.append(None)
                continue

            messages = [
                {
                    "role": "system",
                    "content": sys_prompt},
                {
                    "role": "user",
                    "content": prompt + "\n" + text,
                },
            ]

            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                padding=True,
                pad_to_multiple_of=8,
                return_dict=True,
                return_tensors="pt",
            )

            # move to device ONLY (no forced dtype)
            inputs = inputs.to(self.device)

            input_len = inputs["input_ids"].shape[-1]

            generation = self.model.generate(
                **inputs,
                **self.generation_kwargs,  # no override
            )

            generation = generation[0][input_len:]
            decoded = self.tokenizer.decode(generation, skip_special_tokens=True)

            # optional: try parsing JSON (non-breaking)
            try:
                parsed = json.loads(decoded)
            except Exception:
                parsed = decoded  # fallback to raw string

            results.append(parsed)
        return results

    def cleanup(self, model=False):
        self.cleanup_cuda()
        if model:
            self.cleanup_model(self.model)




