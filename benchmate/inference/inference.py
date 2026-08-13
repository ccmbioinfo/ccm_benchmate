import importlib

import torch
from huggingface_hub import snapshot_download
from benchmate.inference.utils import (Embeddings, ReRank, SemanticChunk, InterpretImage,
                                       ExtractInfo)

def dynamic_import(module_name: str, class_name: str):
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

class Inference:
    def __init__(self, config):
        """Set up all the classes that are in the utils, but not load the models, the models get loaded when
        individual methods are called
        """
        self.config = config
        self.device="cuda" if torch.cuda.is_available() else "cpu"

        self.embeddings=Embeddings(self.config["embedding"]["cache_dir"],
                                   self.config["embedding"]["model_name"],
                                   self.config["embedding"].get("model_kwargs"),
                                   self.config["embedding"].get("processor_kwargs"),
                                   self.config["embedding"].get("quantization_kwargs"),
                                   self.config["embedding"].get("prompt"),
                                   self.device, )


        self.reranker=ReRank(self.config["rerank"]["cache_dir"],
                           self.config["rerank"]["model_name"],
                           self.config["rerank"].get("model_kwargs"),
                           self.config["rerank"].get("processor_kwargs"),
                           self.config["rerank"].get("quantization_kwargs"),
                           prompt=self.config["rerank"].get("prompt"),
                           device=self.device,)

        self.semantic_chunk = SemanticChunk(self.config["semantic_chunk"]["cache_dir"],
                                            **self.config["semantic_chunk"].get("chunking_kwargs", {}),)

        self.image_interpreter = InterpretImage(self.config["interpret_image"]["cache_dir"],
                                                self.config["interpret_image"]["model_name"],
                                                self.config["interpret_image"].get("model_kwargs"),
                                                self.config["interpret_image"].get("processor_kwargs"),
                                                self.config["interpret_image"].get("quantization_kwargs"),
                                                self.config["interpret_image"].get("generation_kwargs"),
                                                dynamic_import("transformers", self.config["interpret_image"]["model_class"]),
                                                dynamic_import("transformers", self.config["interpret_image"]["processor_class"]),
                                                device=self.device )

        self.extract_info = ExtractInfo(self.config["extract_info"]["cache_dir"],
                                        self.config["extract_info"]["model_name"],
                                        self.config["extract_info"].get("model_kwargs"),
                                        self.config["extract_info"].get("tokenizer_kwargs"),
                                        self.config["extract_info"].get("quantization_kwargs"),
                                        self.config["extract_info"].get("generation_kwargs"),
                                        self.config["extract_info"].get("model_class"),
                                        self.device)

    def embed(self, items):
        """
        embed items into embeddings, this can be image, text or both, see utils for a more detailed description
        :param items: a list of items to embed
        :return: a list of embeddings
        """
        embeddings=self.embeddings.encode(items)
        return embeddings

    def rerank(self, query, items):
        """
        given a prompt, a query and a list of items return their re-ranking scores, the items and query can be images, text or both
        :param query: what are we comparing things to
        :param items: list of items to compare
        :return: list of scores in the same order as the items
        """
        scores=self.reranker.rerank(query, items)
        return scores

    def chunk_text(self, text):
        """
        semantically chunk text into chunks, we are using model2vec for speed
        :param text: a large sting
        :return: a list of tuples where (index, text)
        """
        return self.semantic_chunk.chunk_text(text)

    def interpret_image(self, prompt, images):
        """
        create a caption given a system prompt and an image, this is useful for captioning tables or figures
        :param prompt: system prompt to use
        :param images: the image to use
        :return: string of text
        """
        return self.image_interpreter.interpret(sys_prompt=prompt, images=images)

    def text_score(self, query, texts):
        """
        this is a crude text scoring function the query and each text are semantically chunked and each chunk of query
        is compared to every chunk of every text in the texts list. Then we get the max row and colum and take their average
        :param query: what to compare to this
        :param texts: things to compare
        :return: a single float
        """
        query_chunks = [item[1] for item in self.chunk_text(query)]
        if not query_chunks:
            return [0.0] * len(texts)
        query_embeddings = torch.tensor(self.embed(query_chunks))
        scores = []
        for text in texts:
            text_chunks = [item[1] for item in self.chunk_text(text)]
            if not text_chunks:
                scores.append(0.0)
                continue
            text_embeddings = torch.tensor(self.embed(text_chunks))
            similarity_scores = torch.matmul(query_embeddings, text_embeddings.T)
            score = self._symmetric_score(similarity_scores)
            scores.append(score)
        return scores

    def _symmetric_score(self, sim):
        """
        get symetric score for a similarity matrix of a given text and project description
        :param sim: pairwise similarlty matrix of semantic chunks
        :return: float, symmetric score of mean max similarities
        """
        if sim.numel() == 0 or sim.shape[0] == 0 or sim.shape[1] == 0:
            return 0.0
        # Mean of max similarities from rows (text1 to other)
        mean_max_row = torch.max(sim, dim=1).values.mean().item()
        # Mean of max similarities from columns (other to text1)
        mean_max_col = torch.max(sim, dim=0).values.mean().item()
        # Symmetric score
        return (mean_max_row + mean_max_col) / 2

    def gather_models(self, config=None):
        """
        download models from huggingface
        :param config: config file, just the inferece section of config.yaml
        :return: None, but models are downloaded to cache_dir specified in config
        """
        target_config = config if config is not None else self.config
        models=[target_config.get("interpret_image"), target_config.get("embedding"),
                target_config.get("rerank"), target_config.get("semantic_chunk"),
                target_config.get("layout_model")]

        for model in models:
            if not isinstance(model, dict):
                continue
            name = model.get("model_name") or model.get("chunking_model")
            cache_dir = model.get("cache_dir")
            if name and cache_dir:
                snapshot_download(repo_id=name, local_dir=cache_dir)

        return None



