import requests
from Bio import Entrez
from bs4 import BeautifulSoup as bs


# thin wrapper around the NCBI Entrez API and BioPython
class Ncbi:
    def __init__(self, api_key=None, email=None, collect_info=False):
        """
        :param api_key: NCBI API key, you can get one from https://www.ncbi.nlm.nih.gov/account/settings/
        :param email: you can also use your email address if these are not provided the searches will be limited and there will be
        stricter rate limits
        """
        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

        if email is None and api_key is None:
            raise ValueError(
                "No email or API key provided. Please provide an email or API key. Some features may not work or return limited results.")

        self.api_key = api_key
        self.email = email
        databases = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi")
        databases = bs(databases.content, "xml")
        databases = databases.find_all("DbName")
        self.databases = [db.text for db in databases]
        Entrez.email = self.email
        Entrez.api_key = self.api_key

        descriptions={}
        if collect_info:
            dbs= self.show_databses()
            for db in dbs:
                info=self.get_db_info(db)["FieldList"]
                descriptions[db]=info[["FullName", "Description"]]


    def search(self, db, query, retmax=100):
        """
        thin wrapper around the NCBI Entrez esearch
        :param db:
        :param query:
        :param retmax:
        :return:
        """
        stream = Entrez.esearch(db=db, term=query, retmax=retmax)
        record = Entrez.read(stream)
        stream.close()
        ids = record["IdList"]
        return ids

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

    def show_databses(self):
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