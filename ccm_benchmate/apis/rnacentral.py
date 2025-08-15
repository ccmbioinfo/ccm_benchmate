import pandas as pd
import requests



# TODO this needs to be refactored so that id is not passed in the constructor or conver the whole thing to dataclasses
class RnaCentral:
    def __init__(self):
        self.rna_central_api_url = "https://rnacentral.org/api/v1/rna"
        self.headers = {"Content-Type": "application/json"}

    def get_information(self, id: str, get_xrefs: bool = True, get_publications: bool = True):
        """
        Get information about a specific RNAcentral entry.
        :param id: The ID of the entry.
        :return: A dictionary containing information about the entry.
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
                    page_xrefs, xrefs_page = self._get_xrefs(response, id)
                    xrefs.append(page_xrefs)
                response["xrefs"] = pd.concat(xrefs)
            if get_publications:
                publications_page = response["publications"]
                pubs = []
                while publications_page is not None:
                    page_pubs, publications_page = self._get_publications(publications_page)
                    pubs.append(page_pubs)
                response["references"] = pd.concat(pubs)
            return response
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def _get_xrefs(self, response, id: str):
        """
        Get cross-references for a specific RNAcentral entry.
        :return: a dataframe containing cross-references information the modifications section will be a dict not just a string
        or a numeric type
        """
        url=response["xrefs"]
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            response = response.json()
            data = []
            for item in response["results"]:
                results = {}
                for key, value in item.items():
                    if key == "accession":
                        for acc_key, acc_value in value.items():
                            results[acc_key] = acc_value
                    else:
                        results[key] = value
                data.append(results)
            df = pd.DataFrame(data)
            return df, response["next"]
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def _get_publications(self, url):
        """
        :return: a dataframe containing publication information
        """
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            response = response.json()
            papers = response["results"]
            data = []
            for item in papers:
                results = {"title": item["title"],
                           "publication": item["publication"],
                           "pmid": item["pubmed_id"],
                           "doi": item["doi"],
                           "pub_id": item["pub_id"],
                           "expert_db": item["expert_db"], }
                data.append(results)
            df = pd.DataFrame(data)
            return df, response["next"]
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
