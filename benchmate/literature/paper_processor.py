import os
from PIL import Image

import numpy as np
from paddleocr import PaddleOCRVL, PPStructureV3

#this is a two step, 1. we run the regular pipeline and then get all everything, then we check if there is a table, if so
# we run the VL pipeline, we are not extracting references becuse we already get them from openalex
class PaperProcessor:
    def __init__(self, inference, cache_dir=None, device="gpu"):
        """
        Init PaperProcessor, this will prepare and download the models if this is the first time you are using it. Make sure that
        the cache directory exists and is consistent between run otherwise you will end up with multiple copies of the same models
        :param inference: benchmate.inference.inference instance for embedding
        :param cache_dir: cache dir for storing models, this exclusively for paddle ocr models
        :param device: gpu or cpu, not sure if you are ever going to run them on a tpu but that's also supported
        """
        if cache_dir is not None:
            os.environ["PADDLE_HOME"] = cache_dir
        self.ocr_pipeline=PPStructureV3(device=device,
                                        use_doc_unwarping=False,
                                        use_seal_recognition=False,
                                        use_doc_orientation_classify=False,
                                        engine="transformers",
                                        use_chart_recognition=False,
                                        format_block_content=False,
                                        use_table_recognition=False,
                                        use_formula_recognition=True)
        self.vl_pipeline=PaddleOCRVL(device=device,
                                     use_doc_unwarping=False,
                                     use_seal_recognition=False,
                                     use_doc_orientation_classify=False,
                                     engine="transformers",
                                     use_chart_recognition=False,
                                     format_block_content=True,
                                     merge_layout_blocks=True,
                                     layout_merge_bboxes_mode="large")

        self.table_labels=["table"]
        self.text_labels=["text", "abstract", "paragraph_title", "doc_title"]
        self.figure_labels=["image", "chart", "figure_title"]
        self.inference=inference

    def _extract_text(self, results):
        """
        Extract the text from the pdf, this does not include figure captions just the text body
        :param results: results from the parse method
        :return: return a large string that contains the text
        """
        texts=[]
        for page in results:
            for block in page["parsing_res_list"]:
                if block.label in self.text_labels:
                    texts.append(block.content)

        return "\n".join(texts)

    def _extract_figures(self, results):
        """
        Extract figures from a paper, if a figure has multiple panels they will be joined into a single panel
        :param results: results from the pipeline
        :return: returns a dict {"image":<image of the figure>, "text":<figure caption>}. This structure can be
        immediately passed to the VL embedder from inference
        """
        figures = []

        for page in results:
            blocks = page["parsing_res_list"]

            images = [b for b in blocks if b.label in ("image", "chart")]
            captions = [b for b in blocks if b.label == "figure_title"]

            for img in images:
                ix0, iy0, ix1, iy1 = img.bbox
                icx = (ix0 + ix1) / 2

                best_caption = None
                best_score = float("inf")

                for cap in captions:
                    cx0, cy0, cx1, cy1 = cap.bbox
                    ccx = (cx0 + cx1) / 2

                    # vertical preference
                    if cy0 >= iy1:
                        vertical = cy0 - iy1
                    else:
                        vertical = (iy0 - cy1) + 100

                    horizontal = abs(icx - ccx)

                    score = vertical + 0.5 * horizontal

                    if score < best_score:
                        best_score = score
                        best_caption = cap

                if best_caption is None:
                    continue

                figures.append({
                    "image": img.image["img"],
                    "text": best_caption.content if best_caption else None,
                })

        return figures

    def _extract_tables(self, results):
        """
         Extract tables from a paper,
         :param results: results from the pipeline
         :return: returns a dict {"image":<image of the table>, "text":<extracted table content>}. The table content is the
         output of VL model and is parsed like and html. This is by design.
         """
        tables = []

        for page in results:
            for block in page["parsing_res_list"]:

                if block.label == "table":

                    img = np.asarray(block.image["img"])

                    vl_result = self.vl_pipeline.predict(img)

                    # robust extraction for scientific tables
                    text_blocks = []

                    for b in vl_result[0]["parsing_res_list"]:
                        if getattr(b, "content", None):
                            text_blocks.append(b.content)

                    tables.append({
                        "image": block.image["img"],
                        "text": "\n".join(text_blocks) if text_blocks else None,
                    })

        return tables


    def _parse(self, pdf):
        """
        parse a pdf
        :param pdf: a path to a pdf file
        :return: return text, figure and tables in the formats described above
        """
        results=self.ocr_pipeline.predict(input=pdf,
                                         text_det_limit_side_len=4096,
                                         use_e2e_wireless_table_rec_model=True,
                                         text_det_limit_type="max")
        text=self._extract_text(results)
        figures=self._extract_figures(results)
        tables=self._extract_tables(results)

        return text, figures, tables

    def pipeline(self, papers, extract=True, embed_text=True, embed_images=True):
        """
        run the full paper processing pipeline
        :param papers: list of paper class instance
        :param extract: perform the steps in parse
        :param embed_text: semantically chunk and embed the chunks for the full text
        :param embed_images: embed the image and their associated text all in one go using a vl model
        :return: doesnt return anything but fills in the attributes of the paper instances provided

        One thing to note here, if a paper instance has multiple files, it will go through them one by one and perform
        all the actions, there is no check for file order, sometimes the main paper is the first one sometimes not, this
        is especially true if we are downloading the tar file from ncbi, if there is a single oa location in openalex that one is
        preffered. 
        """
        if extract:
            for paper in papers:
                if len(paper.info.file_paths)==1:
                    paper.info.text, paper.info.tables, paper.info.figures = self._parse(paper.info.file_paths[0])
                elif len(paper.info.file_paths) > 1:
                    texts = []
                    figures = []
                    tables = []
                    for file in paper.info.file_paths:
                        text, figs, tbls = self.parse(file)
                        texts.append(text)
                        figures.extend(figs)
                        tables.extend(tbls)
                    texts="\n".join(texts)

                    paper.info.text=texts
                    paper.info.figures=figures
                    paper.info.tables=tables
                elif len(paper.info.file_paths) < 1:
                    raise FileNotFoundError("There are no pdfs associated with this paper did you run paper.download?")

                if embed_text:
                    paper.info.text_chunks = self.inference.chunk_text(paper.info.text)
                    chunks = [{"text": item[1]} for item in paper.info.text_chunks]
                    paper.info.chunk_embeddings = self.inference.embed(chunks)

                if embed_images:
                    if len(paper.info.figures) > 0:
                        embeddings=self.inference.embed_images(paper.info.figures)
                        paper.info.figure_embeddings = embeddings

                    if len(paper.info.tables) > 0:
                        embeddings = self.inference.embed_images(paper.info.tables)
                        paper.info.table_embeddings = embeddings
