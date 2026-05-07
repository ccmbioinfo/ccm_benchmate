import importlib

import torch
from benchmate.inference.utils import (TextRerank, TextEmbed, ImageRerank, ImageEmbed, SemanticChunk, InterpretImage)

def resolve_dotted_object(path):
    """
    Resolve a dotted import path like `transformers.CLIPModel` into the
    actual Python object.
    """
    module_name, attr_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)

class Inference:
    def __init__(self, config):
        self.config = config
        self.device="cuda" if torch.cuda.is_available() else "cpu"
        self.text_embed = TextEmbed(self.config["text_embed"]["cache_dir"],
                                    self.config["text_embed"]["model_name"],
                                    device=self.device,)

        self.text_rerank = TextRerank(self.config["text_rerank"]["cache_dir"],
                                      self.config["text_rerank"]["model_name"],
                                      self.config["text_rerank"]["model_kwargs"],
                                      self.config["text_rerank"]["tokenizer_kwargs"],
                                      device=self.device,
                                     )

        self.image_embed = ImageEmbed(self.config["image_embed"]["cache_dir"],
                                      self.config["image_embed"]["model_name"],
                                      self.config["image_embed"]["model_kwargs"],
                                      self.config["image_embed"]["processor_kwargs"],
                                      resolve_dotted_object(self.config["image_embed"]["model_class"]),
                                      resolve_dotted_object(self.config["image_embed"]["processor_class"]),
                                      device=self.device,)

        self.image_rerank = ImageRerank(self.config["image_rerank"]["cache_dir"],
                                        self.config["image_rerank"]["model_name"],
                                        self.config["image_rerank"]["model_kwargs"],
                                        self.config["image_rerank"]["processor_kwargs"],
                                        resolve_dotted_object(self.config["image_rerank"]["model_class"]),
                                        resolve_dotted_object(self.config["image_rerank"]["processor_class"]),
                                        device=self.device,)

        #self.semantic_chunk = SemanticChunk(self.config["semantic_chunk"]["chunking_model"],
         #                                   **self.config["semantic_chunk"]["chunking_kwargs"],)

#        self.interpret_image = InterpretImage(self.config["interpret_image"]["cache_dir"],
#                                              self.config["interpret_image"]["model_name"],
#                                              self.config["interpret_image"]["model_kwargs"],
#                                              self.config["interpret_image"]["processor_kwargs"],
#                                              resolve_dotted_object(self.config["interpret_image"]["model_class"]),
#                                              resolve_dotted_object(self.config["interpret_image"]["processor_class"]),
#                                              device=self.device )

    #TODO need to check if this is immediately compatible with the db
    def embed_text(self, texts):
        embeddings = self.text_embed.encode(texts)
        return embeddings

    def embed_image(self, images):
        embeddings=self.image_embed(images)
        return embeddings

    def rerank_text(self, query, texts):
        scores=self.text_rerank.rerank(self.config["text_rerank"]["prefix"],
                                self.config["text_rerank"]["suffix"],
                                query, texts)
        return [(score, image) for score, image in sorted(zip(scores, texts), reverse=True)]

    def rerank_image(self, query, images):
        scores=self.image_rerank.rerank(query, images)
        return [(score, image) for score, image in sorted(zip(scores, images), reverse=True)]

    def chunk_text(self, text):
        raise NotImplementedError("Semantic chunking is temporarily disabled in this environment")

    def interpret_image(self, images):
        raise NotImplementedError("Image interpretation is temporarily disabled in this environment")

    def text_score(self, query, texts):
        query_chunks = self.chunk_text(query)
        query_embeddings = self.embed_text(query_chunks)
        query_embeddings = torch.tensor(query_embeddings)
        scores = []
        for text in texts:
            text_chunks = self.chunk_text(text)
            text_embeddings = self.embed_text(text_chunks)
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


