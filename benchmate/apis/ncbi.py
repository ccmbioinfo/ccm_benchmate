import warnings

import requests
from Bio import Entrez
from bs4 import BeautifulSoup as bs

from benchmate.apis.utils import api_call, ApiCall

#TODO this is probably better done via requests
class Ncbi:
    call_class=ApiCall
    def __init__(self, access_key=None, email=None, collect_info=False):
        """
        :param api_key: NCBI API key, you can get one from https://www.ncbi.nlm.nih.gov/account/settings/
        :param email: you can also use your email address if these are not provided the searches will be limited and there will be
        stricter rate limits
        """
        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.links_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elinks.fcgi"
        self.init_kwargs={"access_key":access_key, "email":email, "collect_info":collect_info}

        if email is None and access_key is None:
            raise ValueError(
                "No email or API key provided. Please provide an email or API key. Some features may not work or return limited results.")

        self.api_key = access_key
        self.email = email
        databases = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi")
        databases = bs(databases.content, "xml")
        databases = databases.find_all("DbName")
        self.databases = [db.text for db in databases]
        Entrez.email = self.email
        Entrez.api_key = self.api_key
        descriptions={}
        if collect_info:
            dbs= self.show_databases()
            for db in dbs:
                info=self.get_db_info(db)["FieldList"]
                descriptions[db]=info[["FullName", "Description"]]

    def search(self, db, query, retmax=100):
        """
        thin wrapper around the NCBI Entrez esearch
        :param db: the database to search, use show_databases to see available databases
        :param query: the query string, this can be anything that can be typed into the NCBI search bar
        :param retmax: maximum number of results to return 10000 is the api max
        :return: a list of ncbi ids matching the query from that database the ids are not unique to each database so there can be
        another item with the same id in another database        """
        stream = Entrez.esearch(db=db, term=query, retmax=retmax)
        record = Entrez.read(stream)
        stream.close()
        ids = record["IdList"]
        return ids

    @api_call(lambda self: self.call_class)
    def links(self, from_db, to_db, id):
        linkname=f"{from_db}_{to_db}"
        stream=Entrez.elink(dbfrom=from_db, id=id, linkname=linkname)
        try:
            record=Entrez.read(stream)[0]["LinkSetDb"][0]
        except:
            warnings.warn(f"no connections between {from_db} and {to_db} for {id}")
            return []
        ids=[item["Id"] for item in record["Link"]]
        stream.close()
        return ids

    @api_call(lambda self: self.call_class)
    def summary(self, db, id):
        """
        thin wrapper around the NCBI Entrez esummary
        :param db: db name
        :param id: id to get summary for, you can get the ids from the search function
        :return: list of summary records
        """
        stream = Entrez.esummary(db=db, id=id)
        record = Entrez.read(stream)
        stream.close()
        return record

    @api_call(lambda self: self.call_class)
    def fetch(self, db, id):
        """
        thin wrapper around the NCBI Entrez efetch
        :param db: database name
        :param id: id to fetch
        :return: list parsed from the xml
        """
        stream = Entrez.efetch(db=db, id=id, retmode="xml")
        record = Entrez.read(stream)
        stream.close()
        return record

    def show_databases(self):
        """
        show available databases
        :return: a list of strings of database names, these strings can be used in other functions
        """
        return self.databases

    def get_db_info(self, db):
        """
        get database info
        :param db: name of the database fron show_databases
        :return: list of parameters and how they can be searched
        """
        stream = Entrez.einfo(db=db)
        db_info = Entrez.read(stream)
        record = db_info["DbInfo"]["FieldList"]
        return record