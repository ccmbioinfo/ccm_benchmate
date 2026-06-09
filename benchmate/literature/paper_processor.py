import os
# this is weirdly needed to get tesseract to work
os.environ["TESSDATA_PREFIX"]=f"{os.environ['CONDA_PREFIX']}/share/tessdata"

import torch
import pytesseract

from benchmate.literature.paper_processor_utils import *
from benchmate.inference.inference import Inference


#TODO this now needs to reflect the new inference class
class PaperProcessor:
    """
    paper processor class, this is the main class for extracting text figures and generating embeddings for the papers
    the pipeline method is the main caller where you can specify which steps you would like to run
    all the necessary parameters are passed in a config dict so there are no hard coded values and no values to fill
    """
    def __init__(self, inference:Inference, config):
        """
        Init the paper processor class
        :param inference: this will handle all the processing except for extracting text and figures from the paper that is
        a literature specific task and we do not need to process other items like that.
        :param config: settings related to literature, mostly layout parserstuff
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config=config
        self.inference = inference

    # pass a list of files
    def extract(self, model: LayoutONNX, file_path, cutoff=0.25, zoom=2):
        """
        Extract:
        - full article text (OCR)
        - top-level figures only
        - tables (optional)
        """
        doc = pymupdf.open(file_path)
        texts = []
        figures = []
        tables = []
        for page in doc:
            pix = render_page(page, zoom=zoom)
            W, H = pix.size
            layout, scale, pad = model(pix)
            raw_pictures = []
            table_boxes = []

            for det in layout[0]:
                x1, y1, x2, y2, score, cls_id = det
                if score < cutoff:
                    continue
                cls_id = int(cls_id)
                label = CLASS_NAMES.get(cls_id, "Unknown")

                # scale back from letterbox
                x1, x2 = (x1 - pad[0]) / scale, (x2 - pad[0]) / scale
                y1, y2 = (y1 - pad[1]) / scale, (y2 - pad[1]) / scale
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(W, x2), min(H, y2)
                box = (x1, y1, x2, y2)

                if label == "Picture":
                    raw_pictures.append(box)

                elif label == "Table":
                    table_boxes.append(box)

            #only get the full figure
            filtered_pictures = filter_figures(
                raw_pictures,
                mode="top_level",
                containment_thresh=0.8,
            )

            for b in filtered_pictures:
                figures.append(pix.crop(b))

            for b in table_boxes:
                tables.append(pix.crop(b))

            page_text = pytesseract.image_to_string(pix)
            texts.append(page_text)

        article_text = " ".join(
            t.replace("\n", " ").replace("  ", " ")
            for t in texts
        )

        return article_text, tables, figures

    def pipeline(self, papers, extract=True, embed_text=True, embed_images=True,
                 interpret_images=False):
        """
        whole paper processing pipeline
        :param papers: list of papers see literature.paper for details
        :param extract: extract text, figues and tables (the latter two are images)
        :param embed_text: chunk and embed the pdf text
        :param embed_images: embed images
        :param interpret_images: run a vision language model on the images to generate text
        :param embed_iterpretations: embed the interpretations of the images
        :return: paper class instance with all the attributes filled
        """
        if extract:
            model=LayoutONNX(onnx_path=self.config["layout_model"]["model"])
            for paper in papers:
                paper.info.text, paper.info.tables, paper.info.figures = self.extract(model, paper.info.file_paths)
        else:
            raise NotImplementedError("Extract must be true otherwise there is no data to process")

        if embed_text:
            for paper in papers:
                # the chunked text is a list of lists, since we are chunking one paper at a time the top level will
                paper.info.text_chunks =self.inference.chunk_text(paper.info.text) # to this returns a list of (index, chunk)
                chunks=[{"text":item[1]} for item in paper.info.text_chunks]
                paper.info.chunk_embeddings= self.inference.embed(chunks)

        if embed_images:
            for paper in papers:
                if len(paper.info.figures)>0:
                    figs=[{"image":fig} for fig in paper.info.figures]
                    paper.info.figure_embeddings = self.inference.embed(figs)

                if len(paper.info.tables)>0:
                    tabs=[{"image":table} for table in paper.info.tables]
                    paper.info.table_embeddings = self.inference.embed(tabs)

        if interpret_images:
            for paper in papers:
                paper.info.figure_interpretation = []
                paper.info.table_interpretation = []
                if len(paper.info.figures) > 0:
                    for figure in paper.info.figures:
                        paper.info.figure_interpretation.append(self.inference.interpret_image(figure, self.config["figure_prompt"]))

                if len(paper.info.tables) > 0:
                    for table in paper.info.tables:
                        paper.info.table_interpretation.append(self.inference.interpret_image(table, self.config["table_prompt"]))

            for paper in papers:
                paper.info.figure_interpretation_embeddings = []
                paper.info.table_interpretation_embeddings = []
                if len(paper.info.figure_interpretation) > 0:
                    fig_int=[{"text":int} for int in paper.info.figure_interpretation]
                    paper.info.figure_interpretation_embeddings.append(self.inference.embed(fig_int))

                if len(paper.info.table_interpretation) > 0:
                    tab_int=[{"text":int} for int in paper.info.table_interpretation]
                    paper.info.table_interpretation_embeddings.append(self.inference.embed(tab_int))
        return papers

