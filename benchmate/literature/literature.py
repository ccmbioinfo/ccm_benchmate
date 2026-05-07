import os.path
import time
import tempfile
import requests


from bs4 import BeautifulSoup as bs

from benchmate.literature.utils import *
from benchmate.literature.paperinfo import PaperInfo

class NoPapersError(Exception):
    pass

def paper_from_response(openalex_response):
    """
    generate a paper object from an openalex response
    :param openalex_response: openalex response json
    :return: a paper object
    """
    if "pmid" in openalex_response["ids"].keys():
        paper_id=openalex_response["ids"]["pmid"].split("/").pop()
        id_type="pubmed"
    else:
        raise ValueError("Could not find a valid paper ID in the response.")

    paper=Paper(paper_id=paper_id, id_type=id_type, get_abstract=True)
    paper.info.openalex_info = filter_openalex_response(openalex_response)
    if "best_oa_location" in openalex_response.keys() and openalex_response["best_oa_location"] is not None:
        link = openalex_response["best_oa_location"]["pdf_url"]
        if link is not None and link.endswith(".pdf"):
            download_link = openalex_response["best_oa_location"]["pdf_url"]
        else:
            warnings.warn("Did not find a direct pdf download link")
            download_link = None
    else:
        warnings.warn("There is no place to download the paper, this paper might not be open access")
        download_link = None
    paper.info.download_link = download_link
    return paper


def paper_from_link(link):
    """
    generate a paper object from an openalex link, this is useful for references and related works
    :param link: openalex link
    :return: a paper object
    """
    openalex_id=link.split("/").pop()
    info=search_openalex(paper_id=openalex_id, id_type="openalex")
    paper=paper_from_response(info)
    return paper

class LitSearch:
    def __init__(self, pubmed_api_key=None, email=None, sort_by="relevance"):
        """
        create the ncessary framework for searching
        :param email: email to use for pubmed api
        :param sort_by: relevance or pub+date
        :param pubmed_api_key:
        """
        self.pubmed_key = pubmed_api_key
        self.email=email
        if sort_by not in ["relevance", "pub+date"]:
            raise ValueError("sort_by must be relevance or pub+date")
        self.sorting=sort_by
        self.params={
            "retmode": "xml",
            "email": self.email,
            "api_key": self.pubmed_key,
            "sort": self.sorting,
        }

    def search(self, query, database="pubmed", results="id", max_results=1000):
        """
        search pubmed and arxiv for a query, this is just keyword search no other params are implemented at the moment
        :param query: this is a string that is passed to the search, as long as it is a valid query it will work and other fields can be specified
        :param database: pubmed or arxiv
        :param results: what to return, default is paper id PMID and arxiv id
        :param max_results: max number of results to return default 1000
        :return: paper ids specific to the database
        """
        if database == "pubmed":
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={}&retmax={}".format(query, max_results)
            search_response = requests.get(search_url, params=self.params)
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
    def __init__(self, paper_id, id_type="pubmed", get_abstract=True):
        """
        This class is used to download and process a paper from a given id, it can also be used to process a paper from a file
        :param paper_id:
        :param id_type: pubmed or arxiv
        :param filepath: if you already have the pdf file you can pass it here, mutually exclusive with paper_id
        :param citations: if you want to get the citations for the paper, need paper id, cannot do it with pdf
        :param references: if you want to get the references for the paper, need paper id, cannot do it with pdf
        :param related_works: if you want to get the related works for the paper, need paper id, cannot do it with pdf
        """
        self.info=PaperInfo(paper_id, id_type)
        if get_abstract:
            self.info.abstract, self.info.title, self.info.authors= self.get_abstract()


    #I was wrong, you can have a paper with no authors apparently
    def get_abstract(self):
        """
        get the abstract of the paper from pubmed or arxiv
        :return: fill in the paper info abstract, title, authors
        """
        if self.info.id_type =="pubmed":
            response=requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}".format(self.info.id))
            response.raise_for_status()
            soup=bs(response.text, "xml")
            abstract_text=soup.find("AbstractText")
            if abstract_text is not None:
                abstract_text=abstract_text.text
            else:
                abstract_text=None
            title=soup.find("ArticleTitle").text
            author_tags=soup.find_all("Author")
            if len(author_tags) > 0:
                authors=[]
                for author in author_tags:
                    affiliation_info=author.find("AffiliationInfo")
                    if affiliation_info is not None:
                        if len(affiliation_info.find_all("Affiliation"))>0:
                            authors.append({"name":(author.find("ForeName").text + ", " + author.find("LastName").text),
                                        "affiliation":(author.find("AffiliationInfo").find("Affiliation").text)})
                        else:
                            authors.append({"name": (author.find("ForeName").text + ", " + author.find("LastName").text),
                                            "affiliation": None})
            else:
                authors=None
            article_id_list=soup.find("ArticleIdList")
            if article_id_list is not None:
                pmc_tag=article_id_list.find("ArticleId", IdType="pmc")
                if pmc_tag is not None:
                    pmc_tag=pmc_tag.text
            else:
                pmc_tag=None
            self.info.pmc_id=pmc_tag


        elif self.info.id_type == "arxiv":
            response = requests.get("http://export.arxiv.org/api/query?search_query=id:{}".format(self.info.id))
            response.raise_for_status()
            soup=bs(response.text, "xml")
            abstract_text = soup.find("summary").text
            #not ideal if arxiv changes things, this will break
            title=soup.find_all("title")
            if len(title)==2:
                title=title[1].text
            else:
                title=None
            author_tags = soup.find_all("author")
            authors = []
            if len(author_tags)>0:
                for author in author_tags:
                    authors.append({"name": author.find("name").text,
                                    "affiliation": None})
            else:
                authors=None

        else:
            raise NotImplementedError("source must be pubmed or arxiv other sources are not implemented")

        return abstract_text, title, authors

    def search_info(self, filter_openalex=False):
        """
        Check if pmc id is available, if so build download link from that
        search openalex for the paper info and download link
        :return: fill in the paper info openalex_info and download_link
        """
        download_link = None
        if self.info.pmc_id is not None:
            response = requests.get("https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={}".format(self.info.pmc_id))
            response.raise_for_status()
            soup=bs(response.text, "xml")
            check_error = soup.find("error")
            if check_error is not None:
                warnings.warn("There is no place to download the paper, this paper might not be open access")
                download_link = None
            else:
                pmc_link = soup.find("link", format="tgz")["href"]
                if pmc_link is not None:
                    download_link = pmc_link.replace("ftp://", "https://", 1)

        openalex_info = search_openalex(id_type=self.info.id_type, paper_id=self.info.id, filter=filter_openalex)

        if download_link is None:
            if openalex_info is None:
                warnings.warn("Could not find a paper with id {}".format(self.info.id))

            else:
                if "best_oa_location" in openalex_info.keys() and openalex_info[
                    "best_oa_location"] is not None:
                    link = openalex_info["best_oa_location"]["pdf_url"]
                    if link is not None and link.endswith(".pdf"):
                        download_link = openalex_info["best_oa_location"]["pdf_url"]
                    else:
                        warnings.warn("Did not find a direct pdf download link")
                        download_link = None
                else:
                    warnings.warn("There is no place to download the paper, this paper might not be open access")
                    download_link = None

        self.info.openalex_info=openalex_info
        self.info.download_link=download_link
        return None

    def download(self, destination):
        """
        download the paper pdf to the destination folder
        :param destination: where to download the paper, it must exist, the folder will not be created or checked for existence
        :return: download the paper pdf to the destination folder
        """
        if self.info.download_link.endswith(".tar.gz"):
            tmp_file=tempfile.NamedTemporaryFile(suffix=".tar.gz")
            download_tar(self.info.download_link, tmp_file.name) # downloads into tempfile location
            download_paths=extract_pdfs_from_tar(tmp_file.name, destination) # extracts pdf into destination location

            if len(download_paths) > 1:
                main_paper_path=min(download_paths, key=lambda p: len(os.path.splitext(os.path.basename(p))[0]))
            else:
                main_paper_path=download_paths
            self.info.downloaded=True
            self.info.file_path=main_paper_path
            return None

        download = requests.get(self.info.download_link, stream=True)
        download.raise_for_status()
        if download.headers.get("Content-Type", "").lower() == "application/pdf":
            with open("{}/{}.pdf".format(destination, self.info.id), "wb") as f:
                f.write(download.content)
            file_path=os.path.abspath(os.path.join("{}/{}.pdf".format(destination, self.info.id)))
            self.info.downloaded=True
            self.info.file_path=file_path
        else:
            warnings.warn("Could not download the paper, this paper might not be open access or the link might not point to a pdf file")
        return None


    def get_references(self):
        """
        get the references of the paper from openalex
        :return: fill in the paper info references
        """
        if "referenced_works" not in self.info.openalex_info.keys():
            raise ValueError("The response does not contain references.")
        references=self.info.openalex_info["referenced_works"]
        papers=[]
        for reference in references:
            try:
                p=paper_from_link(reference)
                papers.append(p)
                time.sleep(0.3)
            except:
                print("Could not find a paper with id {}".format(reference.split("/").pop()))

        self.info.references=papers
        return None

    def get_related_works(self):
        """
        get the related works of the paper from openalex
        :return: fill in the paper info related_works
        """
        if "related_works" not in self.info.openalex_info.keys():
            raise ValueError("The response does not contain related works.")
        references = self.info.openalex_info["related_works"]
        papers = []
        for reference in references:
            try:
                p = paper_from_link(reference)
                papers.append(p)
                time.sleep(0.3)
            except:
                print("Could not find a paper with id {}".format(reference.split("/").pop()))
        self.info.related_works=papers
        return None

    def get_cited_by(self, cursor="*"):
        """
        get the papers that cite this paper from openalex
        :param cursor: the used does not need to worry about this, it is used for pagination and recursive calls
        :return: fill in the paper info cited_by
        """
        if "cited_by_api_url" not in self.info.openalex_info.keys():
            raise ValueError("The response does not contain cited by information.")
        url = self.info.openalex_info["cited_by_api_url"] + "&cursor="
        content = requests.get(url + cursor).content.decode().strip()
        content = json.loads(content)
        next_cursor = content["meta"]["next_cursor"]
        papers = []
        if len(content["results"]) > 0:
            for item in content["results"]:
                try:
                    p = paper_from_response(item)
                    papers.append(p)
                    time.sleep(0.3)
                except:
                    print("Could not find a paper with id {}".format(item["ids"]["pmid"].split("/").pop()))
                finally:
                    cursor=next_cursor
            while next_cursor != cursor and next_cursor is not None:
                self.get_cited_by(next_cursor)
            self.info.cited_by=papers
        else:
            warnings.warn("No papers found that cite this work")
            self.info.cited_by=[]
        return None

    def __str__(self):
        return self.info.title

    def __repr__(self):
        return "Paper(id={}, id_type={}, title={})".format(self.info.id, self.info.id_type, self.info.title)

    @classmethod
    def from_kb(cls, project, id):
        info=PaperInfo.from_kb(project, id)
        paper=cls(paper_id=info.id, id_type=info.id_type)
        paper.info=info
        return paper

    def to_kb(self, project):
        return self.info.to_kb(project)
