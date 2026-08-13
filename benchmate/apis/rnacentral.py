import pandas as pd
import requests
from benchmate.apis.utils import api_call, ApiCall


class RnaCentral:
    call_class=ApiCall
    def __init__(self):
        self.rna_central_api_url = "https://rnacentral.org/api/v1/rna"
        self.headers = {"Content-Type": "application/json"}
        self.init_kwargs={}

    @api_call(lambda self: self.call_class)
    def get_information(self, id: str, get_xrefs: bool = True, get_publications: bool = True):
        """
        Get information about a specific RNAcentral entry.
        :param id: rnacentral identifier
        :param get_xrefs: whether to get cross-references form other databases
        :param get_publications: whether to get publications related to the entry, these will return pubmed ids
        :return: a dictionary containing information about the RNAcentral entry
        """
        url = f"{self.rna_central_api_url}/{id}/"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        if response.status_code == 200:
            response = response.json()
            if get_xrefs:
                xrefs_page = response["xrefs"]
                xrefs=[]
                while xrefs_page is not None:
                    page_xrefs, xrefs_page = self._get_xrefs(xrefs_page)
                    xrefs.append(page_xrefs)
                response["xrefs"] = pd.concat(xrefs, ignore_index=True) if xrefs else pd.DataFrame()
            if get_publications:
                publications_page = response["publications"]
                pubs = []
                while publications_page is not None:
                    page_pubs, publications_page = self._get_publications(publications_page)
                    pubs.append(page_pubs)
                response["references"] = pd.concat(pubs, ignore_index=True) if pubs else pd.DataFrame()
            return response
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def _get_xrefs(self, url):
        """
        Get cross-references for a specific RNAcentral entry.
        :return: a dataframe containing cross-references information the modifications section will be a dict not just a string
        or a numeric type
        """
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            res_json = response.json()
            data = []
            for item in res_json["results"]:
                results = {}
                for key, value in item.items():
                    if key == "accession":
                        for acc_key, acc_value in value.items():
                            results[acc_key] = acc_value
                    else:
                        results[key] = value
                data.append(results)
            df = pd.DataFrame(data)
            return df, res_json["next"]
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def _get_publications(self, url):
        """
        :return: a dataframe containing publication information
        """
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            res_json = response.json()
            papers = res_json.get("results", [])
            data = []
            for item in papers:
                results = {"title": item.get("title"),
                           "publication": item.get("publication"),
                           "pmid": item.get("pubmed_id"),
                           "doi": item.get("doi"),
                           "pub_id": item.get("pub_id"),
                           "expert_db": item.get("expert_db")}
                data.append(results)
            df = pd.DataFrame(data)
            return df, res_json.get("next")
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
