import importlib

import torch
from benchmate.inference.utils import (Embeddings, ReRank, SemanticChunk, InterpretImage,
                                       ExtractInfo)

def dynamic_import(module_name: str, class_name: str):
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

class Inference:
    def __init__(self, config):
        self.config = config
        self.device="cuda" if torch.cuda.is_available() else "cpu"

        self.embeddings=Embeddings(self.config["embedding"]["cache_dir"],
                                   self.config["embedding"]["model_name"],
                                   self.config["embedding"]["model_kwargs"],
                                   self.config["embedding"]["processor_kwargs"],
                                   self.config["embedding"]["quantization_kwargs"],
                                   self.config["embedding"]["prompt"],
                                   self.device, )


        self.reranker=ReRank(self.config["rerank"]["cache_dir"],
                           self.config["rerank"]["model_name"],
                           self.config["rerank"]["model_kwargs"],
                           self.config["rerank"]["processor_kwargs"],
                           self.config["rerank"]["quantization_kwargs"],
                           self.config["rerank"]["prompt"],
                           self.device,)

        self.semantic_chunk = SemanticChunk(self.config["semantic_chunk"]["chunking_model"],
                                            **self.config["semantic_chunk"]["chunking_kwargs"],)

        self.interpret_image = InterpretImage(self.config["interpret_image"]["cache_dir"],
                                              self.config["interpret_image"]["model_name"],
                                              self.config["interpret_image"]["model_kwargs"],
                                              self.config["interpret_image"]["processor_kwargs"],
                                              self.config["interpret_image"]["quantization_kwargs"],
                                              dynamic_import("transformers", self.config["interpret_image"]["model_class"]),
                                              dynamic_import("transformers", self.config["interpret_image"]["processor_class"]),
                                              device=self.device )

        self.extract_info = ExtractInfo(self.config["extract_info"]["cache_dir"],
                                        self.config["extract_info"]["model_name"],
                                        self.config["extract_info"]["model_kwargs"],
                                        self.config["extract_info"]["tokenizer_kwargs"],)

    def embed(self, items):
        embeddings=self.embeddings.encode(items)
        return embeddings

    def rerank(self, query, items):
        scores=self.reranker.rerank(query, items)
        return [(score, item) for score, item in sorted(zip(scores, items), reverse=True)]

    def chunk_text(self, text):
        return self.semantic_chunk.chunk_text(text)

    def interpret_image(self, images):
        return self.interpret_image.interpret(images)

    def text_score(self, query, texts):
        query_chunks = [{"type":"text", "text":item[1]} for item in self.chunk_text(query)]
        query_embeddings = self.embed(query_chunks)
        query_embeddings = torch.tensor(query_embeddings)
        scores = []
        for text in texts:
            text_chunks = [{"type":"text", "text":item[1]} for item in self.chunk_text(text)]
            text_embeddings = self.embed(text_chunks)
            text_embeddings = torch.tensor(text_embeddings)
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
        # Mean of max similarities from rows (text1 to other)
        mean_max_row = torch.max(sim, dim=1).values.mean().item()
        # Mean of max similarities from columns (other to text1)
        mean_max_col = torch.max(sim, dim=0).values.mean().item()
        # Symmetric score
        return (mean_max_row + mean_max_col) / 2


