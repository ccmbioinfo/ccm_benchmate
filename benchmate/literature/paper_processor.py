import os
# this is weirdly needed to get tesseract to work
os.environ["TESSDATA_PREFIX"]=f"{os.environ['CONDA_PREFIX']}/share/tessdata"

import torch

import pymupdf
from PIL import Image
import pytesseract
import layoutparser as lp

from chonkie import SemanticChunker, Model2VecEmbeddings
from sentence_transformers import SentenceTransformer

from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from colpali_engine.models import ColPali, ColPaliProcessor

class PaperProcessor:
    """
    paper processor class, this is the main class for extracting text figures and generating embeddings for the papers
    the pipeline method is the main caller where you can specify which steps you would like to run
    all the necessary parameters are passed in a config dict so there are no hard coded values and no values to fill
    """
    def __init__(self, config):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config=config

    # pass a list of files
    def extract(self, model, file_path, zoom=2):
        """
        extract text and images from a pdf, this model gets all the figures and tables from the pdf and returns them as images
        as well as extracting the pdf text using tesseract.
        :param file_path: pdf file path
        :return: text, figures and tables as pillow images
        """
        doc = pymupdf.open(file_path)
        zoom_x = zoom  # horizontal zoom
        zoom_y = zoom  # vertical zoom/
        mat = pymupdf.Matrix(zoom_x, zoom_y)
        texts = []
        figures = []
        tables = []
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            pix = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            layout = model.detect(pix)
            figure_blocks = lp.Layout([b for b in layout if b.type == 'Figure'])
            table_blocks = lp.Layout([b for b in layout if b.type == 'Table'])
            if len(figure_blocks) > 0:
                for block in figure_blocks:
                    coords = block.block
                    coords = (coords.x_1, coords.y_1, coords.x_2, coords.y_2,)
                    figure_img = pix.crop(coords)
                    figures.append(figure_img)

            if len(table_blocks) > 0:
                for block in table_blocks:
                    coords = block.block
                    coords = (coords.x_1, coords.y_1, coords.x_2, coords.y_2,)
                    table_img = pix.crop(coords)
                    tables.append(table_img)

            page_text = pytesseract.image_to_string(pix)
            texts.append(page_text)
        texts = [text.replace("\n", " ").replace("  ", " ") for text in texts]
        article_text = " ".join(texts)

        return article_text, tables, figures


    def text_embeddings(self, chunker, model, text, splitting_strategy="semantic"):
        """
        genereate text embeddings using a chunking strategy and an embedding model. The model is a huggingface senntence transformer
        and the chunker is a chonkie semantic chunker
        :param text: text to embed
        :param chunker: chonkie semantic chunker
        :param splitting_strategy: whether to use semantic chunking or not
        :param embedding_model: sentence transformer model
        :return: chunks and embeddings if not chunked then the whole text and its embedding
        """
        if splitting_strategy == "semantic":
            chunks = chunker.chunk(text)
        elif splitting_strategy == "none":
            chunks = [text]
        else:
            raise NotImplementedError("Semantic splitting and none are the only implemented methods.")
        embeddings = model.encode(chunks)
        return chunks, embeddings


    def image_embeddings(self, images, processor, model):
        batch_images = processor.process_images(images).to(self.device)
        with torch.no_grad():
            image_embeddings = model(**batch_images)

        ems = []
        for i in range(image_embeddings.shape[0]):
            ems.append(image_embeddings[i, :, :])
        return ems

    def interpret_image(self, image, prompt, model, processor, max_tokens=100):
        """
        This function takes an image and a prompt, and generates a text description of the image using a vision-language model.
        the default model is Qwen2_5_VL.
        :param image: PIL image, no need to save to disk
        :param prompt: image prompt, see configs for default
        :param processor: processor class from huggingface
        :param model: model class from huggingface
        :param max_tokens: number of tokens to generate, more tokens = more text but does not mean more information
        :param device: gpu or cpu, if cpu keep it short
        :return: string
        """
        messages = [{"role": "system", "content": [{"type": "text",
                                                    "text": prompt}]},
                    {"role": "user", "content": [{"type": "image", "image": image, }], }]

        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        # this is here for compatibility I will not be processing videos
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.device)
        generated_ids = model.generate(**inputs, max_new_tokens=max_tokens)
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids,
        out_ids in zip(inputs.input_ids, generated_ids)]
        output_text = processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        return output_text

    def pipeline(self, papers, extract=True, embed_text=True, embed_images=True, interpret_images=False, embed_iterpretations=False):
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
            model = lp.Detectron2LayoutModel(   model_path=self.config["lp_model"]["model_path"],
                                            config_path=self.config["lp_model"]["config_path"],
                                            label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
                                            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                                                )
            for paper in papers:
                paper.info.text, paper.info.tables, paper.info.figures = self.extract(model, paper.info.file_path)
        else:
            raise NotImplementedError("Extract must be true otherwise there is no data to process")

        if embed_text:
            chunker_model = Model2VecEmbeddings(self.config["chunker_model"]["model"])
            chunker = SemanticChunker(
                embedding_model=chunker_model,
                threshold=self.config["chunker_model"]["threshold"],
                chunk_size=self.config["chunker_model"]["chunk_size"],
                min_sentences=self.config["chunker_model"]["min_sentences"],
                return_type=self.config["chunker_model"]["return_type"]
            )

            if "config" in self.config["text_embedding_model"].keys():
                text_embedding_kwargs = self.config["text_embedding_model"]["config"]

            model = SentenceTransformer(self.config["text_embedding_model"]["name"],
                                                            **text_embedding_kwargs)
            for paper in papers:
                paper.info.text_chunks, paper.info.chunk_embeddings = self.text_embeddings(chunker, model, paper.info.text, splitting_strategy="semantic")


        if embed_images:
            if "config" in self.config["image_embedding_model"]["model"].keys():
                image_embedding_model_kwargs = self.config["image_embedding_model"]["model"]["config"]

            model = ColPali.from_pretrained(self.config["image_embedding_model"]["model"]["name"],
                                                                 **image_embedding_model_kwargs,
                                                                 torch_dtype=torch.bfloat16,
                                                                 device_map=self.device
                                                                 ).eval()

            if "config" in self.config["image_embedding_model"]["processor"].keys():
                image_embedding_processor_kwargs = self.config["image_embedding_model"]["processor"]["config"]

            processor = ColPaliProcessor.from_pretrained(
                self.config["image_embedding_model"]["processor"]["name"],
                **image_embedding_processor_kwargs, )

            for paper in papers:
                paper.info.figure_embeddings = self.image_embeddings(paper.info.figures, processor, model)
                paper.info.table_embeddings = self.image_embeddings(paper.info.tables, processor, model)

        if interpret_images:
            if "config" in self.config["vl_model"]["model"].keys():
                vl_model_kwargs = self.config["vl_model"]["model"]["config"]

            model = Qwen2_5_VLForConditionalGeneration.from_pretrained(self.config["vl_model"]["model"]["name"],
                                                                        **vl_model_kwargs,
                                                                       device_map=self.device)

            if "config" in self.config["vl_model"]["processor"].keys():
                vl_processor_kwargs = self.config["vl_model"]["processor"]["config"]

            processor = AutoProcessor.from_pretrained(self.config["vl_model"]["processor"]["name"],
                                                              **vl_processor_kwargs)

            for paper in papers:
                paper.info.figure_interpretation = []
                paper.info.table_interpretation = []
                if len(paper.info.figures) > 0:
                    for figure in paper.info.figures:
                        paper.info.figure_interpretation.append(self.interpret_image(figure, self.config["vl_model"]["figure_prompt"], model, processor))

                if len(paper.info.tables) > 0:
                    for table in paper.info.tables:
                        paper.info.table_interpretation.append(self.interpret_image(table, self.config["vl_model"]["table_prompt"], model, processor))


        if embed_iterpretations:
            if not interpret_images:
                raise ValueError("If you want to embed interpretations you must also interpret images")

            # ideally this would not need to re-loaded and all the models will be available all the time
            # but this will save a substantial amount of vram at the cost of couple of seconds of load time
            if "config" in self.config["text_embedding_model"].keys():
                text_embedding_kwargs = self.config["text_embedding_model"]["config"]

            model = SentenceTransformer(self.config["text_embedding_model"]["name"],
                                                            **text_embedding_kwargs)
            # figure and paper interpretations are not chunked, they are embeeded as is, this
            # is not the best but also not that important since the image is embeeded as well and the full text is
            # chunked and embeded

            for paper in papers:
                paper.info.figure_interpretation_embeddings = []
                paper.info.table_interpretation_embeddings = []
                if len(paper.info.figure_interpretation) > 0:
                    for text in paper.info.figure_interpretation:
                        paper.info.figure_interpretation_embeddings.append(
                            self.text_embeddings(chunker=None, model=model, text=text, splitting_strategy="none")
                        )

                if len(paper.info.table_interpretation) > 0:
                    for text in paper.table_interpretation:
                        paper.info.table_interpretation_embeddings.append(
                            self.text_embeddings(chunker=None, model=model, text=text, splitting_strategy="none")
                        )
        return papers