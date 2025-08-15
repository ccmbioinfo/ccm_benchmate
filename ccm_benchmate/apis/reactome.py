import warnings
import requests

# thin wrapper around the api this does comprehensive queries of the knowledge base, does not perform analysis
class Reactome:
    def __init__(self):
        """
        constructor reacotme class, there are not parameters, while getting constructed obtains the latest information from the api
        """
        self.query_url = "https://reactome.org/ContentService/search/query?"
        self.enhanced_url="https://reactome.org/ContentService/data/query/enhanced/"
        self.fields_url="https://reactome.org/ContentService/search/facet"
        response=requests.get(self.fields_url)
        response.raise_for_status()
        response=response.json()
        fields={}
        for facet in response.keys():
            if "Facet" in facet:
                name=facet.replace("Facet","")
                fields[name]=[item["name"] for item in response[facet]["available"]]
            else:
                continue
        self.fields=fields
        self.headers={"Content-Type": "application/json"}

    def query(self, query, species=None, compartments=None, keywords=None, types=None, start=0, num_rows=1000,
              cluster=True, force_filters=True):
        """
        general query that return specific reactome ids for different types
        :param query: a string to be searched
        :param species: a species name see self.show_fields["species"]
        :param compartments: compartment name see self.show_fields["compartment"]
        :param keywords: see self.show_fields["keyword"]
        :param types: see self.show_fields["type"]
        :param start: where to start the search, default is 0
        :param num_rows: number of rows to return default is 1000 (shouldbe more than enough)
        :param cluster: whether the cluster the results by different types default True
        :param force_filters: if True and nothing is found will return an empty dict otherwise will try again w/o any filters
        :return: response dict or an error
        """
        url=self.query_url+"query={}".format(query)
        params={}

        if compartments is not None:
            compartments = self._check_values(compartments, "compartment")
            params["compartments"]=compartments
        if species is not None:
            species = self._check_values(species, "species")
            params["species"]=species
        if keywords is not None:
            keywords = self._check_values(keywords, "keyword")
            params["keywords"]=keywords
        if types is not None:
            types = self._check_values(types, "type")
            params["types"]=types

        if cluster:
            params["cluster"]=cluster

        if force_filters:
            params["force filters"]=force_filters

        params["row"]=start
        params["rows"]=num_rows
        response=requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        response=response.json()
        response=response["results"]
        modified_response={}
        for item in response:
            modified_response[item["typeName"]]=item["entries"]
        return modified_response

    def get_details(self, id):
        """
        get detailed information about a reactome entry, you need the reacotme id
        :param id: reacome id
        :return: response dict
        """
        url=self.enhanced_url+"/{}".format(id)
        response=requests.get(url, headers=self.headers)
        response.raise_for_status()
        response=response.json()
        return response

    def _check_values(self, values, field):
        if type(values) is str:
            values=[values]

        checked_values=[]
        for value in values:
            if value not in self.fields[field]:
                warnings.warn(f"Value {value} not found in fields {self.fields[field]}")
            else:
                checked_values.append(value)
        if len(checked_values) > 0:
            return checked_values
        else:
            return None

    def show_values(self, field):
        if field not in self.fields.keys():
            raise ValueError("That is not one of the available fields, please run show fields")
        else:
            return self.fields[field]

    def show_fields(self):
        return list(self.fields.keys())

    def __str__(self):
        return "Simple reactome api wrapper does not provide any analysis "