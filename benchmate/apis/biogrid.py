import requests
import pandas as pd

from benchmate.apis.utils import api_call, ApiCall


class BioGrid:
    call_class=ApiCall
    def __init__(self, access_key):
        """
        Initialize the BioGrid class with the provided access key.
        :param access_key: you can get one from https://webservice.thebiogrid.org/
        """
        self.access_key = access_key
        self.header = {"Content-Type": "application/json"}
        self.evidence_types = self._get_evidence_types(header=self.header)
        self.organisms=self._get_organisms(header=self.header)
        self.id_types=self._get_supported_identifiers(header=self.header)
        self.init_kwargs={"access_key":self.access_key}

    @api_call(lambda self: self.call_class)
    def interactions(self, gene_list, evidence_types=None, organism=None):
        """
        Get the interactions for the given gene list.
        :param gene_list: list of genes
        :param id_types: the type of the identifier, e.g. "entrez", "uniprot", "ensembl"
        :param evidence_types: see self.evidence_types
        :return: a pandas dataframe with the interactions and kinds of evidences that support them
        """

        url = f"https://webservice.thebiogrid.org/interactions?searcNames=true&geneList{'|'.join(gene_list)}"
        if evidence_types is not None:
            url += f"&evidenceList={'|'.join(evidence_types)}"

        requested_organism=organism
        if requested_organism is not None:
            if requested_organism not in self.organisms.keys():
                if requested_organism not in self.organisms.valuse():
                    raise ValueError(f"Organism {requested_organism} not supported.")
                else:
                    for key in self.requested_organism.keys:
                        if self.organisms[key] == requested_organism:
                            organism = key
            else:
                requested_organism = organism

        url += f"&requestedOrganism={requested_organism}"

        url=f"{url}&format=json&accesskey={self.access_key}"

        response = requests.get(url, headers=self.header)
        if response.status_code == 200:
            data = response.json()
            results=[]
            for interaction, values in data.items():
                results.append(values)
            df = pd.DataFrame(results)
            return df
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def _get_evidence_types(self, header):
        """
        Get the evidence types from BioGrid.
        :return: A list of evidence types.
        """
        url = f"https://webservice.thebiogrid.org/evidence/?accessKey={self.access_key}&format=json"
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            return response.content.decode().split("\n")
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def _get_organisms(self, header):
        """
        Get the organisms from BioGrid.
        :return: A list of organisms.
        """
        url = f"https://webservice.thebiogrid.org/organisms/?accessKey={self.access_key}&format=json"
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            return response.content.decode().split("\n")
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def _get_supported_identifiers(self, header):
        """
        Get the supported identifiers from BioGrid.
        :return: A list of supported identifiers.
        """
        url = f"https://webservice.thebiogrid.org/identifiers/?accesskey={self.access_key}&format=json"
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            return response.content.decode().split("\n")
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")