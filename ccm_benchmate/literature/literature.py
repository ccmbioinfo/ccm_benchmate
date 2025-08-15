import os.path
import warnings

from bs4 import BeautifulSoup as bs

from ccm_benchmate.literature.utils import *

class NoPapersError(Exception):
    pass

class LitSearch:
    def __init__(self, pubmed_api_key=None):
        """
        create the ncessary framework for searching
        :param pubmed_api_key:
        """
        self.pubmed_key = pubmed_api_key

    #TODO advanced search, while technically supported because query is just a string it would be nice if it was explicit
    def search(self, query, database="pubmed", results="id", max_results=1000):
        """
        search pubmed and arxiv for a query, this is just keyword search no other params are implemented at the moment
        :param query: this is a string that is passed to the search, as long as it is a valid query it will work and other fields can be specified
        :param database: pubmed or arxiv
        :param results: what to return, default is paper id PMID and arxiv id
        :param max_results:
        :return: paper ids specific to the database
        """
        #TODO implement pubmed api key for non-free papers
        if database == "pubmed":
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={}&retmax={}".format(query, max_results)
            search_response = requests.get(search_url)
            search_response.raise_for_status()

            soup = bs(search_response.text, "xml")
            ids = [item.text for item in soup.find_all("Id")]

            if results == "doi":
                dois = []
                for paperid in ids:
                    response = requests.get(
                        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}".format(paperid))
                    response.raise_for_status()
                    soup = bs(response.text, "xml")
                    dois.append([item.text for item in soup.find_all("ArticleId") if item.attrs["IdType"] == "doi"])
                to_ret=dois
            else:
                to_ret=ids

        elif database == "arxiv":
            search_url="http://export.arxiv.org/api/search_query?{}&max_results={}".format(query, str(max_results))
            search_response = requests.get(search_url)
            search_response.raise_for_status()
            soup = bs(search_response.text, "xml")
            ids=[item.text.split("/").pop() for item in soup.find_all("id")][1:] #first one is the search id
            to_ret= ids
        return to_ret


class Paper:
    def __init__(self, paper_id, id_type="pubmed", search_openalex=True, citations=True,
                 references=True, related_works=True):
        """
        This class is used to download and process a paper from a given id, it can also be used to process a paper from a file
        :param paper_id:
        :param id_type: pubmed or arxiv
        :param filepath: if you already have the pdf file you can pass it here, mutually exclusive with paper_id
        :param citations: if you want to get the citations for the paper, need paper id, cannot do it with pdf
        :param references: if you want to get the references for the paper, need paper id, cannot do it with pdf
        :param related_works: if you want to get the related works for the paper, need paper id, cannot do it with pdf
        """
        self.paper_id = paper_id
        self.id_type = id_type
        self.table_interpretation = None
        self.figure_interpretation = None
        self.figure_interpretation_embeddings=None
        self.table_interpretation_embeddings = None
        self.tables = None
        self.figures = None
        self.text = None
        self.text_chunks = None
        self.chunk_embeddings = None
        self.abstract = self.get_abstract()
        self.abstract_embeddings = None
        if search_openalex:
            self.paper_info = search_openalex(id_type=self.id_type, paper_id=self.id, cited_by=citations,
                                              references=references, related_works=related_works)
            if self.paper_info is None:
                raise NoPapersError("Could not find a paper with id {}".format(self.id))

            if "best_oa_location" in self.paper_info.keys() and self.paper_info["best_oa_location"] is not None:
                link = self.paper_info["best_oa_location"]["pdf_url"]
                if link is not None and link.endswith(".pdf"):
                    self.download_link = self.paper_info["best_oa_location"]["pdf_url"]
                else:
                    warnings.warn("Did not find a direct pdf download link")
                    self.download_link = None
            else:
                warnings.warn("There is no place to download the paper, this paper might not be open access")
                self.download_link = None


    def get_abstract(self):
        abstract_text=None
        if self.id_type =="pubmed":
            response=requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}".format(self.paper_id))
            response.raise_for_status()
            soup=bs(response.text, "xml")
            abstract=soup.find("AbstractText")
            if abstract is not None:
                abstract_text = soup.find("AbstractText").text

        elif self.id_type == "arxiv":
            response = requests.get("http://export.arxiv.org/api/query?search_query=id:{}".format(self.paper_id))
            response.raise_for_status()
            soup=bs(response.text, "xml")
            abstract_text = soup.find("summary").text
        else:
            raise NotImplementedError("source must be pubmed or arxiv other sources are not implemented")

        return abstract_text

    def download(self, destination):
        download = requests.get(self.download_link, stream=True)
        download.raise_for_status()
        with open("{}/{}.pdf".format(destination, self.id), "wb") as f:
            f.write(download.content)
        file_paths=os.path.abspath(os.path.join("{}/{}.pdf".format(destination, self.id)))
        return file_paths

    def process(self, file_path, embed_images=True, embed_text=True, embed_interpretations=True, **kwargs):
        """
        see utils.py for details
        :return:
        """
        article_text, figures, tables, figure_interpretation, table_interpretation = process_pdf(file_path)
        self.text=article_text
        self.figures=figures
        self.tables=tables
        self.figure_interpretation=figure_interpretation
        self.table_interpretation=table_interpretation

        if embed_images:
            if len(self.figrues) > 0:
                figure_embeddings=[]
                for fig in self.figures:
                    figure_embeddings.append(image_embeddings(fig, **kwargs))

            if len(self.tables) > 0:
                table_embeddings=[]
                for table in self.tables:
                    table_embeddings.append(embed_images, table, **kwargs)

        if embed_text:
            self.abstract_embeddings=text_embeddings(self.abstract, splitting_stratety="none")[1]
            if self.text is not None:
                self.text_chunks, self.chunk_embeddings=text_embeddings(self.text,
                                                                        splitting_stratety="semantic",
                                                                        **kwargs)

            if self.figure_interpretation is not None:
                self.figure_interpretation_embeddings=text_embeddings(self.figure_interpretation,
                                                                      splitting_strategy="none")[1]

            if self.table_interpretation is not None:
                self.table_interpretation_embeddings=text_embeddings(self.table_interpretation,
                                                                      splitting_strategy="none")[1]

        return self

    def __str__(self):
        return self.paper_info["title"]






