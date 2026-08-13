from dataclasses import dataclass
from functools import cached_property
from time import sleep

import requests
import xmltodict

class EbiClientError(Exception):
    pass

class EbiClientWarning(Warning):
    pass

client_dict={
    "pepinfo": {"description": "pepinfo sequence statistics",
                "url":"https://www.ebi.ac.uk/Tools/services/rest/emboss_pepinfo",
                "type":"protein"},
    "pepstats": {"description": "pepstats sequence statistics and plots",
                 "url":"https://www.ebi.ac.uk/Tools/services/rest/emboss_pepstats",
                 "type":"protein"},
    "pepwindow":{"description": "pepwindow sequences statistics and plots",
                 "url":"https://www.ebi.ac.uk/Tools/services/rest/emboss_pepwindow",
                 "type":"protein"},
    "isochore":{"description": "isochore nucleotide sequence statistics and plots",
                 "url":"https://www.ebi.ac.uk/Tools/services/rest/emboss_isochore",
                 "type":"nucleotide"},
    "hmmscan":{"description": "hmmscan Protein function analysis with HMMER 3 hmmscan",
               "url":"https://www.ebi.ac.uk/Tools/services/rest/hmmer3_hmmscan",
               "type":"protein"},
    "nhmmer": {"description": "Sequence similarity search with HMMER3 nhmmer",
                "type": "nucleotide",
               "url": "https://www.ebi.ac.uk/Tools/services/rest/hmmer3_nhmmer"},
    "phmmer": {"description": "Protein function analysis with HMMER 3 phmmer",
                "url": "https://www.ebi.ac.uk/Tools/services/rest/hmmer3_phmmer",
                "type": "protein"},
    "cmscan": {"description": "RNA analysis with Infernal CM Scan",
               "url": "https://www.ebi.ac.uk/Tools/services/rest/infernal_cmscan",
               "type": "nucleotide"},
    "iprscan": {"description": "Protein function analysis with InterProScan 5",
               "url": "https://www.ebi.ac.uk/Tools/services/rest/iprscan5",
               "type": "protein"},
    "pfamscan": {"description": "Protein function analysis with PfamScan",
               "url": "https://www.ebi.ac.uk/Tools/services/rest/pfamscan",
               "type": "protein"},
    "phobius": {"description": "Protein function analysis with Phobius",
               "url": "https://www.ebi.ac.uk/Tools/services/rest/phobius",
               "type": "protein"},
    "pratt": {"description": "Protein function analysis with Pratt",
               "url": "https://www.ebi.ac.uk/Tools/services/rest/pratt",
               "type": "protein"},
    "radar": {"description": "Protein function analysis with Radar",
               "url": "https://www.ebi.ac.uk/Tools/services/rest/radar",
               "type": "protein"},
    "saps": {"description": "Sequence statistics and plots with SAPS",
               "url": "https://www.ebi.ac.uk/Tools/services/rest/saps",
               "type": "protein"},
}

class BaseClient:
    """
    Base class for EBI clients, not sure if double level abstraction is necessary but I wanted to be defensive, this way
    if there are differences between clients, I can implement them in subclasses
    """
    def __init__(self, base_url, email):
        """
        for longer running jobs ebi clients require an email address, this is used to send notifications
        :param base_url: This comes from the client_dict
        :param email:
        """
        self.base_url=base_url
        self.email=email

    @cached_property
    def params(self):
        """
        thankfully each client has an enpoint that returns the parameters, and then you can get the details of each parameter
        using param_details
        :return: returns a list of parameters
        """
        response = requests.get(f"{self.base_url}/parameters")
        if response.status_code != 200:
            raise EbiClientError(f"Failed to get parameters {response.status_code}")
        else:
            return xmltodict.parse(response.text)["parameters"]


    def param_details(self, param_name):
        """
        for a given parameter name, return the details and what type it is, what it does etc.
        :param param_name: str, name of the param from BaseClient.params
        :return:
        """
        response = requests.get(f"{self.base_url}/parameterdetails/{param_name}")
        if response.status_code != 200:
            raise EbiClientError(f"Failed to get parameter details {response.status_code}")
        else:
            return xmltodict.parse(response.text)["parameter"]

class Client(BaseClient):
    """
    This is here for defensive purposes, I cannot predict the future
    """
    def __init__(self, base_url, name, description, email):
        super().__init__(base_url, email)
        self.name=name
        self.description=description

    def run(self, params):
        """
        run the client with the given parameters
        :param params: dict, parameters to pass to the client you can see what they are from BaseClient.params
        :return: Job object instance see below
        """
        params["email"]=self.email
        response = requests.post(f"{self.base_url}/run", data=params)
        if response.status_code != 200:
            raise EbiClientError(f"Failed to run {response.status_code}")
        else:
            id=response.text
            return Job(self, id, params)


    def __repr__(self):
        return f"<Client {self.name}:{self.description}>"

    def __str__(self):
        return self.name


@dataclass
class Job:
    """
    and ebi client job, depending on th submission the results might take a few seconds to a few minutes to be ready.
    """
    client: Client
    id: str
    params: dict
    result_type: str = None
    results: bytes = None

    @property
    def status(self):
        """
        query the status of the job
        :return: simple string, one of QUEUED, RUNNING, FINISHED if failed you will get an EbiClientError
        """
        response = requests.get(f"{self.client.base_url}/status/{self.id}")
        if response.status_code != 200:
            raise EbiClientError(f"Failed to get status {response.status_code}")
        else:
            return response.text

    @cached_property
    def result_types(self):
        """
        each client can return multiple result types, this is a list of those result types
        :return: list of dicts, each dict has the identifier and description you will need to pass the "identifier" to get the results
        """
        response = requests.get(f"{self.client.base_url}/resulttypes/{self.id}")
        if response.status_code != 200:
            raise EbiClientError(f"Failed to get result types {response.status_code}")
        else:
            return xmltodict.parse(response.text)["types"]

    @property
    def result_names(self):
        return [item["identifier"] for item in self.result_types["type"]]

    def get_results(self, type):
        """
        get the results of your job in the format you want.
        :param type: type of the result, these vary, from MSA, to html, to xml to image and other formats, because of this
        feature they will not be integrated into kb but will be thing that stands on its own like alphagenome
        :return: this is raw bytes, if you know you are getting a text you can parse it but there is no guarantee or standard
        text mode, you may need your own parsers.
        """
        types=[item["identifier"] for item in self.result_types["type"]]
        if type not in types:
            raise EbiClientError(f"Result type {type} not found for job {self.id}. Available types: {types}")

        if self.status == "FINISHED":
            response = requests.get(f"{self.client.base_url}/result/{self.id}/{type}")
            if response.status_code != 200:
                raise EbiClientError(f"Failed to get results {response.status_code}")
            else:
                result = response.content
                self.result_type=type
                self.results=result
                return result

        elif self.status=="QUEUED" or self.status=="RUNNING":
            warnings.warn("Job is not finished yet", EbiClientWarning)
            return None


class DbFetchClient:
    """
    dbfetch is a universal query endpoint for ebi, it hosts many databases and can be used to query them. The downside is
    you need to know what you want, that is you can only query databases for specific ids.
    """
    def __init__(self):
        self.base_url="https://www.ebi.ac.uk/Tools/dbfetch/dbfetch"

    @cached_property
    def databases(self):
        """
        get the databases that are available for querying
        :return: a dict mapping database name to database info
        """
        response = requests.get(f"{self.base_url}/dbfetch.databases?style=json")
        if response.status_code != 200:
            raise EbiClientError(f"Failed to get databases {response.status_code}")
        else:
            data = response.json()
            if isinstance(data, dict) and "dbInfoList" in data:
                return {db["name"]: db for db in data["dbInfoList"] if isinstance(db, dict) and "name" in db}
            elif isinstance(data, list):
                return {db["name"]: db for db in data if isinstance(db, dict) and "name" in db}
            return data

    def fetch_data(self, database:str, id:str, format:str="default", style:str="raw"):
        """
        get some results from a database of your choosing
        :param database: which database
        :param id: the id of the thing you want
        :param format: which format you want it returned in, pdb, msa etc. these change depending on the database,
        DbFetchClient.databases will tell you what formats are available for each database.
        :param style: which style you want it, defautl is raw, the options are usually html and raw.
        :return: DBFetchData instance
        """
        if database not in self.databases:
            raise EbiClientError(f"Database {database} not found")

        db_info = self.databases[database]
        db_supported_formats = list(set([item["name"] for item in db_info.get("formatInfoList", []) if "name" in item]))
        if format != "default" and db_supported_formats and format not in db_supported_formats:
            raise EbiClientError(f"Format {format} not found for database {database}. Available formats: {db_supported_formats}")

        db_supported_styles = list(set([item["name"] for item in db_info.get("styleInfoList", []) if "name" in item]))
        if style != "raw" and db_supported_styles and style not in db_supported_styles:
            raise EbiClientError(
                f"Style {style} not found for database {database}. Available styles: {db_supported_styles}")

        response = requests.get(f"{self.base_url}/dbfetch?db={database};id={id};format={format};style={style}")
        if response.status_code != 200:
            raise EbiClientError(f"Failed to fetch data {response.status_code}")
        else:
            return DbFetchData(database, id, format, style, response.content)

@dataclass
class DbFetchData:
    database:str
    id:str
    format:str
    style:str
    data:bytes #there are many formats, this is raw bytes, you will need to parse it


class EBI:
    """
    this is a thin wrapper around the above classes
    """
    def __init__(self, email: str = "user@example.com"):
        self.dbfetch = DbFetchClient()
        self.clients = {}
        for name, info in client_dict.items():
            self.clients[name] = Client(info["url"], name, description=info["description"], email=email)

    @property
    def dbfetch_databses(self):
        """
        get a list of all available databases
        """
        return self.dbfetch.databases

    def search_database(self, query, database, format="default", style="raw"):
        """
        search a database
        :param query: what to search for
        :param database: which database to search
        :param format: format of output
        :param style: style of output
        :return: see dbfetchclient.fetch_data
        """
        return self.dbfetch.fetch_data(database=database, id=query, format=format, style=style)

    @property
    def ebi_clients(self):
        """
        get a list of all available clients
        """
        return list(self.clients.keys())

    def run_client(self, client_name, params):
        """
        run a client see Client
        """
        return self.clients[client_name].run(params)

    def get_client_params(self, client_name):
        """
        get client parameters that it supports see Client
        """
        return self.clients[client_name].params

    def get_client_param_details(self, client_name, param_name):
        """
        get details about a client param see Client
        """
        return self.clients[client_name].param_details(param_name)

    def get_client_status(self, client_job):
        """Check the status of a client job"""
        return client_job.status

    def get_client_result_types(self, client_job):
        """Get the result types of a client job"""
        return client_job.result_types

    def get_client_result(self, client_job, result_type):
        """Get the result of a client job"""
        return client_job.get_results(result_type)

    def __repr__(self):
        return f"EBI with dbfetch and {len(self.clients)} clients"

    def __str__(self):
        return f"EBI with dbfetch and {len(self.clients)} clients"
