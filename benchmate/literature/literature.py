from dataclasses import dataclass
import os.path
import time
import tempfile
from time import sleep
from math import ceil
import warnings

import pandas as pd

from benchmate.literature.utils import *
from benchmate.literature.paperinfo import PaperInfo
from benchmate.utils.general_utils import warn_for_status

class NoPapersError(Exception):
    pass

def paper_from_response(response, openalex=None, get_references=False,
                        get_related_papers=False, get_cited_by=False):
    """
    take an openalex response and convert that to a paper object
    :param response: response json
    :param openalex: OpenAlex client instance required if fetching references/cited_by
    :param get_references: whether to return references or not
    :param get_related_papers: whether to return related papers or not
    :param get_cited_by: whether to return cited papers or not
    :return: paper object
    """
    paper_id=response["id"].split("/")[-1]
    paper=Paper(paper_id=paper_id)
    paper.info.full_json=response
    paper.parse_json()
    if openalex is not None:
        if get_references:
            paper.get_references(openalex)
        if get_related_papers:
            paper.get_related_works(openalex)
        if get_cited_by:
            paper.get_cited_by(openalex)
    return paper

def paper_from_id(openalex, id, id_type, get_references=False, get_related_papers=False, get_cited_by=False):
    """
    for an id type (instead of openalex id) this function will return a paper object, this can be useful when you are trying to
    collect information from other sources like a uniprot api call
    :param openalex: openalex
    :param id: the actual id
    :param id_type: type of the id, pmid, full doi url, pmcid or magid
    :param get_references: as the name suggests
    :param get_related_papers: as the name suggests
    :param get_cited_by: as the name suggests
    :return: a paper object instance, this call paper_from_response under the hood
    """
    ids=["doi", "pmid", "pmcid", "magid"]
    if id_type not in ids:
        raise NoPapersError(f"only, {','.join(ids)} are supported")

    else:
        pid=f"{id_type}:{id}"
        params={
            "api_key":openalex.api_key
        }

        headers = {
            'Accept': 'application/json'
        }
        response=requests.get(f"https://api.openalex.org/works/{pid}", params=params, headers=headers)
        response.raise_for_status()
        response=response.json()
        paper=paper_from_response(response, openalex=openalex, get_references=get_references, get_related_papers=get_related_papers,
                                  get_cited_by=get_cited_by)
        return paper


def paper_from_link(link, openalex,get_references=False,
                        get_related_papers=False, get_cited_by=False):
    """
    generate a paper object from an openalex link, this is useful for references and related works
    :param link: openalex link
    :return: a paper object
    """
    openalex_id=link.split("/").pop()
    paper=Paper(paper_id=openalex_id)
    paper.get_json(openalex)
    paper.parse_json()
    if get_references:
        paper.get_references(openalex)
    if get_related_papers:
        paper.get_related_works(openalex)
    if get_cited_by:
        paper.get_cited_by(openalex)
    return paper

@dataclass
class OpenAlex:
    """just storing basic information about openalex, this includes the link and yourj api key"""
    api_key: str
    paper_url: str = "https://api.openalex.org/works"


class LitSearch:

    sort_fields=["relevance", "cited_by_count", "publication_date"]
    return_fields=["title", "abstract", "doi", "publication_date", "venue"]

    def _process_query(self, query, joiner="and"):
        """
        given a query format it in a way that is compatible with openalex
        :param query: query either str or a list of str
        :param joiner: and or or, this is used to join the strings and then will affect search results
        :return: a string to be passed to search
        """
        if isinstance(query, list):
            processed = []
            for item in query:
                item = str(item)
                if " " in item.strip():
                    item = f'"{item}"'
                processed.append(item)

            return f" {joiner} ".join(processed)

        elif isinstance(query, str):
            query = query.strip()
            if " " in query:
                return f'"{query}"'
            return query

        raise TypeError("query must be a string or a list of strings")


    def search(self, openalex, pos_query, pos_joiner="and", neg_query=None, neg_joiner="or", fields=["title", "abstract", "doi", "publication_date", "venue"],
               sort_by="relevance", max_results=10000):
        """
        search pubmed and arxiv for a query, this is just keyword search no other params are implemented at the moment
        :param query: this is a string that is passed to the search, as long as it is a valid query it will work and other fields can be specified
        :param database: pubmed or arxiv
        :param results: what to return, default is paper id PMID and arxiv id
        :param max_results: max number of results to return default 1000
        :return: paper ids specific to the database
        """
        pos_query=self._process_query(pos_query, pos_joiner)

        if neg_query:
            neg_query=self._process_query(neg_query, neg_joiner)
            query=f'({pos_query}) not ({neg_query})'
        else:
            query=pos_query

        if sort_by not in self.sort_fields:
            raise NotImplementedError(f"Only {','.join(self.sort_fields)} are supported")

        new_fields=[]
        to_ret=[]
        for field in fields:
            if field not in self.return_fields:
                warnings.warn(f"{field} is not a valid field and will be ignored")
            elif field=="abstract":
                new_fields.append(field)
                to_ret.append("abstract_inverted_index")
            elif field=="venue":
                new_fields.append(field)
                to_ret.append("primary_location")
            else:
                new_fields.append(field)
                to_ret.append(field)

        if sort_by=="relevance":
            sort="relevance_score"
        elif sort_by=="publication_date":
            sort="publication_date"
        elif sort_by=="cited_by_count":
            sort="cited_by_count"

        to_ret.append("id")
        to_ret.append(sort)
        to_ret=list(set(to_ret))

        params={
            "search":query,
            "select":",".join(to_ret),
            "sort":sort+":desc",
            "per_page":200,
            "api_key":openalex.api_key
        }

        headers = {
            'Accept': 'application/json'
        }

        results=requests.get(openalex.paper_url, params=params, headers=headers)
        warn_for_status(results, "Problem getting search results")
        response=results.json()

        meta=response["meta"]
        hits=meta["count"]
        if hits>max_results:
            pages=ceil(max_results/200)
        else:
            pages=ceil(hits/200)

        papers=response["results"]
        for i in range(1, pages):
            params["page"]=i
            results = requests.get(openalex.paper_url, params=params, headers=headers)
            results.raise_for_status()
            papers.extend(results.json()["results"])
            if i > 100:
                sleep(1)

        new_fields.append("id")
        for_df={}
        for item in new_fields:
            if item=="id":
                ids=[paper["id"].split("/").pop() for paper in papers]
                for_df[item]=ids
            elif item=="title":
                titles=[paper["title"] for paper in papers]
                for_df[item]=titles
            elif item=="abstract":
                abstracts=[reconstruct_abstract(paper["abstract_inverted_index"]) for paper in papers]
                for_df[item]=abstracts
            elif item=="doi":
                dois=[paper["doi"] for paper in papers]
                for_df[item]=dois
            elif item=="is_oa":
                is_oa=[paper["is_oa"] for paper in papers]
                for_df[item]=is_oa
            elif item=="venue":
                venues=[paper["primary_location"]["raw_source_name"] for paper in papers]
                for_df[item]=venues

        df=pd.DataFrame(for_df)
        return df


class Paper:
    def __init__(self, paper_id):
        """
        This class is used to download and process a paper from a given id, it can also be used to process a paper from a file
        :param paper_id: openalex id of the paper
        """
        self.info=PaperInfo(id=paper_id)

    def get_json(self, openalex):
        """
        for a given paper id query openalex api and get the detailed information
        :param openalex: openalex instance, see above
        :return: json from openalex
        """
        params={
            "api_key": openalex.api_key
        }

        headers = {
            'Accept': 'application/json'
        }
        paper_url=f"{openalex.paper_url}/{self.info.id}"
        info=requests.get(paper_url, headers=headers, params=params)
        info.raise_for_status()
        info=info.json()
        self.info.full_json=info

    def parse_json(self):
        """
        parse the json and extract the most useful information into separate fields
        :return: paper.info instance filled in for the attrs that are defined explicitly
        """
        self.info.title=self.info.full_json["title"]
        self.info.abstract=reconstruct_abstract(self.info.full_json["abstract_inverted_index"])
        self.info.external_ids=self.info.full_json["ids"]
        self.info.publication_date=self.info.full_json["publication_date"] if "publication_date" in self.info.full_json.keys() else None
        self.info.venue=self.info.full_json["primary_location"]["raw_source_name"] if "primary_location" in self.info.full_json.keys() else None
        self.info.doi=self.info.full_json["doi"]
        self.info.authors=[]
        for item in self.info.full_json["authorships"]:
            self.info.authors.append(item["author"]["display_name"])

        self.info.download_links=[]

        if self.info.full_json["open_access"]["is_oa"]:
            if self.info.full_json["has_content"]["pdf"]:
                self.info.download_links.append(self.info.full_json["content_urls"]["pdf"])
            if self.info.full_json["locations_count"] > 0:
                for i in range(self.info.full_json["locations_count"]):
                    loc = self.info.full_json["locations"][i]
                    if loc["pdf_url"] is not None:
                        self.info.download_links.append(loc["pdf_url"])


    def download(self, destination):
        """
        download the paper pdf to the destination folder
        :param destination: where to download the paper, it must exist, the folder will not be created or checked for existence
        :return: download the paper pdf to the destination folder
        """
        downloaded=False
        for link in self.info.download_links:
            if link.endswith(".tar.gz"):
                tmp_file=tempfile.NamedTemporaryFile(suffix=".tar.gz")
                download_tar(link, tmp_file.name) # downloads into tempfile location
                download_paths=extract_pdfs_from_tar(tmp_file.name, destination, self.info.id)

                if len(download_paths) > 1:
                    main_paper_path=[min(download_paths, key=lambda p: len(os.path.splitext(os.path.basename(p))[0]))]
                else:
                    main_paper_path=download_paths if isinstance(download_paths, list) else [download_paths]
                self.info.file_paths=main_paper_path
                downloaded=True
                return None
            elif link.endswith(".pdf"):
                download = requests.get(link, stream=True)
                try:
                    download.raise_for_status()
                    if download.headers.get("Content-Type", "").lower() == "application/pdf":
                        out_path = os.path.abspath(os.path.join(destination, f"{self.info.id}.pdf"))
                        with open(out_path, "wb") as f:
                            f.write(download.content)
                        self.info.file_paths=[out_path]
                        downloaded=True
                        break
                except Exception as e:
                    warnings.warn(f"Could not download the paper from link {link}: {e}")
                    continue
                finally:
                    download.close()
        if not downloaded:
            warnings.warn(f"Could not download the paper, from any of the {len(self.info.download_links)} links")

    def get_references(self, openalex):
        """
        get the references of the paper from openalex
        :return: fill in the paper info references
        """
        if "referenced_works" not in self.info.full_json.keys():
            raise ValueError("The response does not contain references.")
        references=self.info.full_json["referenced_works"]
        papers=[]
        for reference in references:
            try:
                p=paper_from_link(reference, openalex)
                papers.append(p)
                time.sleep(0.1)
            except Exception as e:
                print("Could not find a paper with id {}: {}".format(reference.split("/").pop(), e))

        self.info.references=papers
        return None

    def get_related_works(self, openalex):
        """
        get the related works of the paper from openalex
        :return: fill in the paper info related_works
        """
        if "related_works" not in self.info.full_json.keys():
            raise ValueError("The response does not contain related works.")
        references = self.info.full_json["related_works"]
        papers = []
        for reference in references:
            try:
                p = paper_from_link(reference, openalex)
                papers.append(p)
                time.sleep(0.3)
            except Exception as e:
                print("Could not find a paper with id {}: {}".format(reference.split("/").pop(), e))
        self.info.related_works=papers
        return None

    def get_cited_by(self, openalex):
        """
        get the papers that cite this paper from openalex
        :param cursor: the used does not need to worry about this, it is used for pagination and recursive calls
        :return: fill in the paper info cited_by
        """
        params={
            "filter":f"cites:{self.info.id}",
            "per_page":200,
            "api_key":openalex.api_key
        }

        headers = {
            'Accept': 'application/json'
        }

        content = requests.get(openalex.paper_url, params=params, headers=headers).json()
        meta=content["meta"]
        cited_by=content["results"]

        if meta["count"] > 10000:
            total=10000
        else:
            total=meta["count"]

        pages=ceil(total/200)

        if pages>1 and len(cited_by)>0:
            for i in range(1, pages):
                params = {
                    "filter": f"cites:{self.info.id}",
                    "per_page": 200,
                    "api_key": openalex.api_key,
                    "page": i
                }
                results=requests.get(openalex.paper_url, params=params, headers=headers).json()
                cited_by.extend(results["results"])

        cited_papers=[]
        for paper in cited_by:
            p=paper_from_response(paper)
            cited_papers.append(p)

        self.info.cited_by=cited_papers
        return cited_papers

    def process(self, processor, extract=True, embed_text=True, embed_images=True):
        """
        run the paper processor pipeline
        :param processor: processor class instance
        :param extract: extract text, figures and tables from the pdf
        :param embed_text: chunk and embed the paper text
        :param embed_images: embed figures and tables
        :return: filled in paper info, doesnt return anything but fills inplace
        """
        if self.info.file_paths is None:
            raise ValueError("The paper pdf has not been downloaded yet, run paper.download()")
        else:
            file_paths = self.info.file_paths if isinstance(self.info.file_paths, list) else [self.info.file_paths]
            if len(file_paths) < 1:
                raise ValueError("The paper pdf has not been downloaded yet, run paper.download()")
            processed = processor.pipeline([self], extract, embed_text, embed_images)
            self.info = processed[0].info


    def __str__(self):
        return self.info.title

    def __repr__(self):
        return "Paper(id={}, title={})".format(self.info.id, self.info.title)

