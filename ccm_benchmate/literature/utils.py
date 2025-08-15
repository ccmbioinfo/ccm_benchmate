import tarfile
import warnings
import time

from PIL import Image
import pytesseract
import layoutparser as lp

import pymupdf
import torch
import requests
import json

from adapters import AutoAdapterModel
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, AutoTokenizer
from qwen_vl_utils import process_vision_info
from chonkie import SemanticChunker, Model2VecEmbeddings
from colpali_engine.models import ColPali, ColPaliProcessor


from ccm_benchmate.literature.configs import *
from ccm_benchmate.utils.general_utils import *

def interpret_image(image, prompt, processor, model, max_tokens, device):
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
    prompt[1]["content"][0]["image"] = image
    text = processor.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True)
    # this is here for compatibility I will not be processing videos
    image_inputs, video_inputs = process_vision_info(prompt)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(device)
    generated_ids = model.generate(**inputs, max_new_tokens=max_tokens)
    generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids,
    out_ids in zip(inputs.input_ids, generated_ids)]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    return output_text

#TODO add tables test a paper with wester/northern blots
#TODO alternate method to include paper abstract
def process_pdf(pdf, lp_model=paper_processing_config["lp_model"], interpret_figures=True, interpret_tables=True,
                vl_model=paper_processing_config["vl_model"], zoomx=2, device="cuda", max_tokens=400, figure_prompt=figure_messages,
                table_prompt=table_message):
    """
    This function takes a pdf file and processes it using layout parser and pytesseract to extract text, figures and tables.
    figures and tables are PIL instances, text is a string. the text is then chunked into smaller pieces using the chunking strategy
    the default is semantic chunking. This is preprocessing for the a RAG application
    :param pdf:
    :param lp_model:
    :param interpret_figures: whether to interpret figures or not using vision language model
    :param interpret_tables: whether to interpret tables or not using vision language model
    :param vl_model:
    :param zoomx: zoom factor for the pdf, higher means better quality but slower processing important for OCR
    :param device: better be GPU
    :param max_tokens:
    :param figure_prompt: see configs for default it makes a difference
    :param table_prompt:
    :return:
    """
    lp_model=lp.Detectron2LayoutModel(lp_model["config"], lp_model["model"],
                             label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
                             extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                             )

    doc = pymupdf.open(pdf)
    zoom_x = zoomx  # horizontal zoom
    zoom_y = zoomx  # vertical zoom
    mat = pymupdf.Matrix(zoom_x, zoom_y)
    texts = []
    figures = []
    tables=[]
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        pix = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        layout = lp_model.detect(pix)
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
    texts=[text.replace("\n", " ").replace("  ", " ") for text in texts]
    article_text = " ".join(texts)

    if interpret_figures or interpret_tables:
        model_vl = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            vl_model, torch_dtype="auto", device_map="auto"
        )
        processor = AutoProcessor.from_pretrained(vl_model)

    figure_interpretation = []
    if interpret_figures:
        for figure in figures:
            figure_interpretation.append(interpret_image(figure, figure_prompt, processor, model_vl, max_tokens, device,))

    table_interpretation = []
    if interpret_tables:
        for table in tables:
            table_interpretation.append(interpret_image(table, table_prompt, processor, model_vl, max_tokens, device,))

    return article_text, figures, tables, figure_interpretation, table_interpretation


def image_embeddings(images, model_dir=paper_processing_config["image_embedding_model"], device="cuda:0"):

    model = ColPali.from_pretrained(
        model_dir,
        torch_dtype=torch.bfloat16,
        device_map=device,  # or "mps" if on Apple Silicon
    ).eval()
    processor = ColPaliProcessor.from_pretrained(model_dir)
    batch_images = processor.process_images(images).to(model.device)
    with torch.no_grad():
        image_embeddings = model(**batch_images)

    ems = []
    for i in range(image_embeddings.shape[0]):
        ems.append(image_embeddings[i, :, :])
    return ems


# same model for article text and captions
def text_embeddings(text, splitting_strategy="semantic",
               params=paper_processing_config["chunking"]):

    embeddings = Model2VecEmbeddings(params["model"])

    if splitting_strategy == "semantic":
        chunker = SemanticChunker(
            embedding_model=embeddings,
            threshold=params["threshold"],  # Similarity threshold (0-1) or (1-100) or "auto"
            chunk_size=params["chunk_size"],  # Maximum tokens per chunk
            min_sentences=params["min_sentences"],  # Initial sentences per chunk,
            return_type=params["return_type"]  # return a list of strings
        )
        chunks = chunker.chunk(text)

    elif splitting_strategy == "none":
        chunks=[text]
    else:
        raise NotImplementedError("Semantic splitting and none are the only implemented methods.")

    embeddings = []
    for chunk in chunks:
        model = AutoAdapterModel.from_pretrained(params["text_embedding_model"])
        model.load_adapter(params["text_embedding_model"]+"/adapter",
                           source="hf", load_as="specter2", set_active=True)
        tokenizer = AutoTokenizer.from_pretrained(params["text_embedding_model"])
        inputs = tokenizer(chunk, padding=True, truncation=True,
                           return_tensors="pt",
                           return_token_type_ids=False, max_length=512)
        output = model(**inputs)
        output=output.last_hidden_state[0]
        #get mean embedding
        ems=torch.mean(output, dim=0)
        embeddings.append(ems)
    return chunks, embeddings

# At this point this is almost legacy because pmc ids are not a reliable source of retrieval. When we can find them
# they come in tar.gz format so here we are.
def extract_pdfs_from_tar(file, destination):
    """Lists the contents of a .tar.gz file.
    Args:
        file_path: The path to the .tar.gz file.
    """
    if not os.path.exists(destination):
        raise FileNotFoundError("{} does not exist.".format(destination))

    try:
        if file.endswith(".tar.gz"):
            read_str="r:gz"
        elif file.endswith(".tar.bz2"):
            read_str="r:bz2"
        elif file.endswith(".zip"):
            read_str="r:zip"
        else:
            read_str="r"

        paths=[]
        with tarfile.open(file, read_str) as tar:
            for member in tar.getmembers():
                if member.name.endswith("pdf"):
                    tar.extract(member, destination)
                    paths.append(os.path.abspath(os.path.join(destination, file, member.name)))

        return paths

    except FileNotFoundError:
        print(f"Error: File not found: {file}")
        return None

    except tarfile.ReadError:
        print(f"Error: Could not open or read {file}. It might be corrupted or not a valid tar.gz file.")
        return None

#This is not for the end user, this is for the developers
def filter_openalex_response(response, fields=None):
    if fields is None:
        fields=["id", "doi", "title", "topics", "keywords", "concepts",
                "mesh", "best_oa_location", "referenced_works", "related_works",
                "cited_by_api_url", "datasets"]
    new_response = {}
    for field in fields:
        if field in response.keys():
            new_response[field] = response[field]
    return new_response


#currenlt using this because semantich scholar has not given me an api key, I emailed them multiple times
# openalex does not have abstracts but we already have functions to get them from arxiv and pubmed
def search_openalex(id_type, paper_id, fields=None, cited_by=False, references=False, related_works=False):
    base_url = "https://api.openalex.org/works/{}"
    if id_type == "doi":
        paper_id = f"https://doi.org/:{paper_id}"
    elif paper_id == "MAG":
        paper_id = f"mag:{paper_id}"
    elif id_type == "pubmed":
        paper_id = f"pmid:{paper_id}"
    elif id_type == "pmcid":
        paper_id = f"pmcid:{paper_id}"

    url = base_url.format(paper_id)
    response = requests.get(url)
    try:
        response = json.loads(response.content.decode().strip())
        new_response = filter_openalex_response(response, fields)

        if cited_by:
            if "cited_by_api_url" in new_response.keys():
                time.sleep(1)
                cited_by=requests.get(new_response["cited_by_api_url"])
                cited_by.raise_for_status()
                cited_by = json.loads(cited_by.content.decode().strip())
                cited_by = cited_by["results"]
                cited_by_list = []
                for cited in cited_by:
                    cited_by_list.append(filter_openalex_response(cited, fields))
                new_response["cited_by"] = cited_by_list

        if references:
            new_response["reference_details"]=[]
            count=0
            counter= len(new_response["referenced_works"]) if len(new_response["referenced_works"])<10 else 10
            while count < counter:
                for i in range(len(new_response["referenced_works"])):
                    ref_id=new_response["referenced_works"][i].split("/").pop()
                    url=base_url.format(ref_id)
                    ref=requests.get(url)
                    ref.raise_for_status()
                    ref=json.loads(ref.content.decode().strip())
                    count=count+1
                    ref=filter_openalex_response(ref, fields)
                    new_response["reference_details"].append(ref)
            else:
                time.sleep(1)
    except:
        warnings.warn("Could not find a paper with the given ID.")
        new_response=None

    if related_works and new_response is not None:
        new_response["related_works_details"]=[]
        count=0
        counter = len(new_response["related_works"]) if len(new_response["related_works"]) < 10 else 10
        while count < counter:
            for i in range(len(new_response["related_works"])):
                ref_id=new_response["related_works"][i].split("/").pop()
                url=base_url.format(ref_id)
                ref=requests.get(url)
                ref.raise_for_status()
                ref=json.loads(ref.content.decode().strip())
                count=count+1
                ref=filter_openalex_response(ref, fields)
                new_response["related_works_details"].append(ref)
        else:
            time.sleep(1)

    return new_response

# its here, not sure if I will use it
def search_semantic_scholar(paper_id, id_type, api_key=None, fields=None):
    base_url="https://api.semanticscholar.org/graph/v1/paper/{}?fields={}"
    if id_type == "doi":
        paper_id=f"DOI:{paper_id}"
    elif id_type == "arxiv":
        paper_id=f"ARXIV:{paper_id}"
    elif paper_id == "mag":
        paper_id=f"MAG:{paper_id}"
    elif id_type == "pubmed":
        paper_id=f"PMID:{paper_id}"
    elif id_type == "pmcid":
        paper_id=f"PMCID:{paper_id}"
    elif id_type == "ACL":
        paper_id=f"ACL:{paper_id}"

    available_fields=["paperId", "corpusID", "externalIds", "url", "title", "abstract", "venue",
                      "publicationVenue", "year", "referenceCount", "citationCount", "influentialCitationCount",
                      "isOpenAccess", "openAccessPdf", "fieldsOfStudy", "s2FieldsOfStudy",
                      "publicationTypes", "publicationDate", "journal", "citationStyles", "authors",
                      "citations", "references", "embedding", "tldr"]
    acceptable_fields=[]
    for field in fields:
        if field in available_fields:
            acceptable_fields.append(field)
        else:
            warnings.warn("field '{}' not available".format(field))

    if api_key is not None:
        headers = {
            'X-API-Key': api_key,
            'Accept': 'application/json'
        }
    url=base_url.format(paper_id, ",".join(acceptable_fields))
    response = requests.get(url)
    response.raise_for_status()
    response=json.loads(response.content.decode().strip())
    return response