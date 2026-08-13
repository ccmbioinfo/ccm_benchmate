import time
from functools import cached_property
from dataclasses import dataclass
import requests
from typing import Dict, Optional, Any

from benchmate.apis.utils import api_call, ApiCall


class TooManyResultsError(Exception):
    pass

@dataclass
class Ontology:
    """
    Dataclass to store ontology term information. Same idea as the other dataclasses, this actually not used because
    it get converted to dict later on, it's here for convenience
    """
    term_id: str = None
    ontology_id: str = None
    details: Dict[str, Any] = None
    children: list = None
    parents: list = None
    descendants: list = None
    ancestors: list =None
    graph: dict =None


class OLS:
    call_class=ApiCall
    """
    ontology Lookup Service (OLS) client for querying ontology information, because I have avoided
    dealing with owl files and will continue to do so.
    """
    def __init__(self):
        self.base_url= "https://www.ebi.ac.uk/ols4/api"
        self.init_kwargs={}

    @cached_property
    def ontologies(self):
        """
        get a list of all ontologies in OLS, this may take a few seconds to run the first time around but after that it will be cached
        """
        url = self.base_url + "/ontologies"
        ontologies = {}

        #for recursion
        def _fetch_page(url):
            page_ont = {}
            response  = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for ontology in data['_embedded']['ontologies']:
                page_ont[ontology['ontologyId']] = {}
                page_ont[ontology['ontologyId']]['title'] = ontology['config']['title']
                page_ont[ontology['ontologyId']]['description'] = ontology['config'].get('description', '')
                page_ont[ontology['ontologyId']]["prefix"] = ontology['config'].get('preferredPrefix', '')
                page_ont[ontology['ontologyId']]["number_of_terms"] = ontology.get('numberOfTerms', 0)
                page_ont[ontology['ontologyId']]["number_of_properties"] = ontology.get('numberOfProperties', 0)
                page_ont[ontology['ontologyId']]["number_of_individuals"] = ontology.get('numberOfIndividuals', 0)
                page_ont[ontology['ontologyId']]["terms"] = ontology["_links"]["terms"]["href"] if "terms" in ontology.get("_links", {}) else ""
                page_ont[ontology['ontologyId']]["properties"] = ontology["_links"]["properties"]["href"] if "properties" in ontology.get("_links", {}) else ""
                page_ont[ontology['ontologyId']]["individuals"] = ontology["_links"]["individuals"]["href"] if "individuals" in ontology.get("_links", {}) else ""
            if 'next' in data.get('_links', {}):
                next_url = data['_links']['next']['href']
            else:
                next_url = None

            return page_ont, next_url

        while url is not None:
            page_ont, url = _fetch_page(url)
            time.sleep(0.3)  # Be polite and avoid overwhelming the server
            ontologies.update(page_ont)

        return ontologies

    @api_call(lambda self: self.call_class)
    def get_term(self, ontology_id: str, term_id: str, iri: Optional[str] = None, get_children: bool = False,
                    get_parents: bool = False, get_ancestors=False, get_descendants=False, get_graph=False):
        """
        get details about a specific term in an ontology, you will need to know the ontology id and either the term id or the iri
        :param ontology_id: name of the ontology to search
        :param term_id: the short form, or term id can be used
        :param iri: or you can use the full iri
        :param get_children: get the children, these will not be recursuve in the sense that it will just return the json, not additional
        ontology objects
        :param get_parents: same as children but for parents
        :param get_ancestors: same as children but for ancestors
        :param get_descendants: same as children but for descendants
        :param get_graph: get the relationship graph for the term, this is just a dict of the graph {"nodes": [], "edges": []}
        :return: ontology object with details and requested features
        """
        identifier_to_use = iri if iri else term_id
        search_url = f"{self.base_url}/ontologies/{ontology_id}/terms"
        params = {'iri': identifier_to_use}
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        details=data.get("_embedded", {})
        terms = details.get("terms", [])
        if len(terms) == 1:
            results=Ontology(
                term_id=term_id,
                ontology_id=ontology_id,
                details=terms[0],
            )
            if get_children:
                results.children=self._get_feature(ontology=results, feature="children")

            if get_parents:
                results.parents=self._get_feature(ontology=results, feature="parents")

            if get_ancestors:
                results.ancestors=self._get_feature(ontology=results, feature="ancestors")

            if get_descendants:
                results.descendants=self._get_feature(ontology=results, feature="descendants")

            if get_graph:
                results.graph=self._get_feature(ontology=results, feature="graph")

            return results.__dict__
        elif len(terms) == 0:
            raise ValueError(f"No term found for {term_id} in ontology {ontology_id}.")
        else:
            raise TooManyResultsError(f"Multiple terms found for {term_id} in ontology {ontology_id}.")


    def _get_feature(self, ontology:Ontology, feature:str):
        if "_links" not in ontology.details or feature not in ontology.details["_links"]:
            return [] if feature != "graph" else {}
        url = ontology.details["_links"][feature]["href"]
        if feature in ["children", "parents", "ancestors", "descendants"]:
            data=[]
            while url is not None:
                results, url=self._get_recursive(url)
                data.extend(results)
                time.sleep(0.3)
        elif feature=="graph":
            response = requests.get(url)
            response.raise_for_status()
            data=response.json()
        else:
            raise ValueError(f"Feature {feature} not recognized.")
        return data

    @staticmethod
    def _get_recursive(url):
        response = requests.get(url)
        response.raise_for_status()
        data= response.json()
        results = data.get("_embedded", {}).get("terms", [])
        if '_links' in data and 'next' in data['_links']:
            next_url = data['_links']['next']['href']
        else:
            next_url = None
        return results, next_url
