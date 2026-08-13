import pandas as pd
import json

import requests

from benchmate.utils.general_utils import *
from benchmate.apis.utils import api_call, ApiCall

class UniProt:
    call_class=ApiCall
    def __init__(self):
        """
        constructor for the UniProt class, which is used to gather data from the UniProt API. and process it in a readable format.
        """
        self.url = "https://www.ebi.ac.uk/proteins/api/proteins?accession={}"
        self.search_url="https://rest.uniprot.org/uniprotkb/search"
        self.headers = {'Accept': 'application/json'}
        self.init_kwargs={}

    def _gather(self, uniprot_id):
        """
        This function gathers data from the UniProt API using the provided uniprot_id.
        :param uniprot_id: uniprot accession
        :return: whole json response from the API
        """
        response = requests.get(self.url.format(uniprot_id), headers=self.headers)
        content = warn_for_status(response, "issues with gathering data")
        if content is not None:
            content = json.loads(content)
            if len(content) > 1:
                raise ValueError("Your query returned more than one result please check your accession")
            else:
                content = content[0]

        return content


    def search(self, query, page_size=500):
        """
        free text query for the uniprot api
        :param query: text query, anything that can be searched on the uniprot website
        :param page_size: number of items per request, this is not the total number of results, it will get results until
        there are no more pages
        :return: a dataframe of name, uniprot id, gene name, organism and a brief description
        """
        params = {
            "query": query,
            "fields": ["accession", "protein_name", "gene_names", "organism_name"],
            "includeIsoform": "false",
            "size": str(page_size)
        }
        next_url = self.search_url
        results=[]
        done=False
        while not done:
            response = requests.get(next_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            for item in data["results"]:
                desc=[]

                if "recommendedName" in item["proteinDescription"].keys():
                    desc.append(item["proteinDescription"]["recommendedName"]["fullName"]["value"])
                elif "submissionNames" in item["proteinDescription"].keys():
                    desc.append(item["proteinDescription"]["submissionNames"][0]["fullName"]["value"])

                if "alternativeNames" in item["proteinDescription"].keys():
                    desc.append([name["fullName"]["value"] for name in item["proteinDescription"]["alternativeNames"]])
                #desc = ",".join(desc)
                syns = None
                if "genes" in item.keys():
                    if "geneName" in item["genes"][0].keys():
                        gene=item["genes"][0]["geneName"]["value"]
                        if "synonyms" in item["genes"][0].keys():
                            syns=[x["value"] for x in item["genes"][0]["synonyms"]]
                        else:
                            syns=[]
                    else:
                        gene=None
                else:
                    gene=None

                item_result= {"id": item["primaryAccession"], "gene": gene, "description": desc,
                              "synonyms": syns if isinstance(syns, list) else None,
                              "organism": item["organism"]["scientificName"]}

                results.append(item_result)

            if "link" not in response.headers.keys():
                done=True
            else:
                next_url = response.headers["link"].split(";")[0].replace("<", "").replace(">", "")
                params=None
        return results

    @api_call(lambda self: self.call_class)
    def get_info(self, uniprot_id, consolidate_refs=True, get_variations=True,
                       get_interactions=True, get_mutagenesis=True, get_isoforms=True):
        """
        gather all the information about a specific entry described by the uniprot id
        :param uniprot_id: uniprot accession
        :param consolidate_refs: whether to consolidate all the references from the different sections into a single list
        :param get_variations: whether to call the variations api
        :param get_interactions: whether to call the interactions api
        :param get_mutagenesis: whether to call the mutagenesis api
        :param get_isoforms: whether to call the isoforms api
        :return:
        """
        id = uniprot_id
        res_json=self._gather(uniprot_id)
        sequence = res_json["sequence"]["sequence"]
        organism = {"name": res_json["organism"]['names'], "taxid": res_json["organism"]["taxonomy"]}

        gene = res_json.get('gene')
        feature_types = set()
        if "features" in res_json.keys():
            feature_types = set([feat['type'] for feat in res_json["features"]])

        comment_types = set()
        if "comments" in res_json.keys():
            comment_types = set([feat["type"] for feat in res_json['comments']])

        references = self._extract_references(res_json)
        xref_types, xrefs = self._extract_xrefs(res_json)


        if "recommendedName" in res_json["protein"].keys():
            name = res_json["protein"]['recommendedName']["fullName"]['value']
            description = self._extract_description(res_json)
        else:
            name = res_json["protein"]['submittedName']["fullName"]['value']
            description = None

        results = {"id": id, "name": name, "sequence": sequence, "organism": organism, "gene": gene,
                   "feature_types": feature_types, "comment_types": comment_types, "references": references,
                   "xref_types": xref_types, "xrefs": xrefs, "description": description, "json": res_json,}

        if "secondaryAccession" in res_json.keys():
            secondary_accessions = [res_json["secondaryAccession"]]
            results["secondary_accessions"] = secondary_accessions

        if "alternativeNames" in res_json.keys():
            alternative_names = res_json['alternativeNames']
            results["alternative_names"] = alternative_names

        if get_variations:
            variation = self._get_variations(results)
            results["variation"] = variation

        if get_interactions:
            interactions =Interactions(results).gather()
            results["interactions"] = interactions

        if get_mutagenesis:
            mutagenesis = Mutagenesis(results).gather()
            results["mutagenesis"] =mutagenesis

        if get_isoforms:
            isoforms = Isoforms(results).gather()
            results["isoforms"] = isoforms

        if consolidate_refs:
            references = self._consolidate_references(results)
            results["references"] = references["references"]

        return results

    def _extract_description(self, results):
        """
        concanate the comments from the json response into a single string this can be used in nlp tasks or comparing
        uniprot instances this is an internal function
        :return: a string that concats all the comments as a description
        """
        desc = []
        for comment in results.get("comments", []):
            if "text" in comment.keys():
                desc.append("\n".join([item["value"] for item in comment["text"] if type(item)==dict]))
        description = "\n".join(desc)
        return description

    def _extract_references(self, results):
        """
        internal function to extract references from the json response, this is an internal function
        :return: references
        """
        refs = []
        for reference in results.get("references", []):
            if "dbReferences" in reference.get("citation", {}):
                for db in reference["citation"]["dbReferences"]:
                    if db.get("type") in ["PubMed"]:
                        refs.append(db["id"])

        return refs

    def _extract_xrefs(self, results):
        """
        internal function to extract xrefs from the json response this is an internal function
        :return: xref types and xrefs
        """
        xrefs = results.get("dbReferences", [])
        xref_types = list(set([item["type"] for item in xrefs if "type" in item]))
        return xref_types, xrefs

    def get_features(self, results, feature_types=None):
        """
        filter already extracted features by type, this just filters the features from the json response
        :param feature_types: type of the feature to filter by
        :return: the features
        """
        raw_features = results.get("json", {}).get("features", [])
        if feature_types is not None:
            features = [feat for feat in raw_features if feat.get("type") in feature_types]
        else:
            features = list(raw_features)
        return features

    def get_comments(self, results, types=None):
        """
        get already extracted comments from the json response
        :param types: comment types to filter by
        :return: comments
        """
        raw_comments = results.get("json", {}).get("comments", [])
        if types is not None:
            if type(types) == str:
                types = [types]
            comments = [comment for comment in raw_comments if comment.get("type") in types]
        else:
            comments = list(raw_comments)
        return comments

    def _get_variations(self, results):
        """
        query the uniprot API for variations
        :return: list of variation dictionaries
        """
        url = 'https://www.ebi.ac.uk/proteins/api/variation?offset=0&size=-1&accession={}'
        variants = requests.get(url.format(results["id"]), headers=self.headers)
        content = warn_for_status(variants, "issues with getting variation")
        if content is None:
            return []
        parsed = json.loads(content)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed[0].get("features", [])
        return []

    def _consolidate_references(self, results):
        """
        pul all references from the isoforms, mutagenesis, interactions and variations into a single list this is useful
        for literature mining and other tasks, this is an internal function
        :return: references
        """

        if "isoforms" in results.keys() and results["isoforms"] is not None:
            for isoform in results["isoforms"]:
                for refs in isoform.get("pubmed_id", []):
                    results["references"].append(refs)

        if "mutagenesis" in results.keys() and results["mutagenesis"] is not None:
            for mut in results["mutagenesis"]:
                if isinstance(mut, dict) and "pubmed_id" in mut and mut["pubmed_id"]:
                    for ref in mut["pubmed_id"]:
                        results["references"].append(ref)

        if "variation" in results.keys() and results["variation"] is not None:
            for var in results["variation"]:
                if isinstance(var, dict) and "evidences" in var:
                    for ev in var.get("evidences", []):
                        if isinstance(ev, dict) and "source" in ev and isinstance(ev["source"], dict):
                            if ev["source"].get("name", "").lower() == "pubmed" and "id" in ev["source"]:
                                results["references"].append(ev["source"]["id"])

        results["references"]=list(set(results["references"]))
        return results


class Interactions:
    def __init__(self, uniprot):
        """
        query the uniprot API for interaction data
        :param uniprot: uniprot class
        """
        self.uniprot_id = uniprot["id"]
        self.url = 'https://www.ebi.ac.uk/proteins/api/proteins/interaction/{}'
        self.headers = {'Accept': 'application/json'}

    def gather(self):
        response = requests.get(self.url.format(self.uniprot_id), headers=self.headers)
        content = warn_for_status(response, "issues with gathering interaction data from intact")
        if content is not None:
            content = json.loads(content)[0]["interactions"]
        interactions = content
        return interactions



class Isoforms:
    def __init__(self, uniprot):
        """
        query the uniprot API for isoform data not all proteins have isoforms and there will be warnings if none are found
        :param uniprot: uniprot class
        """
        self.uniprot_id = uniprot["id"]
        self.url = 'https://www.ebi.ac.uk/proteins/api/proteins/{}/isoforms'
        self.headers = {'Accept': 'application/json'}

    def gather(self):
        isoforms = []
        isoforms_response = requests.get(self.url.format(self.uniprot_id), headers=self.headers)
        if isoforms_response.status_code != 200:
            warnings.warn("Did not find any isoforms for {}".format(self.uniprot_id))
            isoforms = None
        else:
            isoforms_response = json.loads(isoforms_response.content.decode())
            for iso in isoforms_response:
                accession = iso["accession"]
                comments = [comment["type"] for comment in iso["comments"]]
                sequence = iso["sequence"]["sequence"]
                external_references = iso["dbReferences"]
                ref_ids = []
                references = [ref for ref in iso["references"]]
                for ref in references:
                    reftypes = ref.get("citation", {})
                    if "dbReferences" in reftypes:
                        for rtype in reftypes["dbReferences"]:
                            if isinstance(rtype, dict):
                                if rtype.get("type") in ["PubMed", "Pubmed"]:
                                    ref_ids.append(rtype["id"])
                isoform = {"accession": accession, "comments": comments, "sequence": sequence, "pubmed_id": ref_ids,
                           "external_references": external_references, }
                isoforms.append(isoform)
            isoforms = isoforms
        return isoforms


class Mutagenesis:
    def __init__(self, uniprot):
        """
        query the uniprot API for mutagenesis data this is different than variations, these are not variations that are
        seen in the wild but from experimental data
        :param uniprot: uniprot class
        """
        self.uniprot_id = uniprot["id"]
        self.url = 'https://www.ebi.ac.uk/proteins/api/mutagenesis?offset=0&size=-1&accession={}'
        self.headers = {'Accept': 'application/json'}

    def gather(self):
        mutations = []
        mutations_response = requests.get(self.url.format(self.uniprot_id), headers=self.headers)
        mutations_response = warn_for_status(mutations_response, "issues with gathering mutagenesis data")
        mutations_response = json.loads(mutations_response)
        if mutations_response is not None and len(mutations_response) > 0:
            mutations_response = mutations_response[0]["features"]
            for mutation in mutations_response:
                type = mutation["type"]
                alt = mutation["alternativeSequence"]
                start = mutation["begin"]
                end = mutation["end"]
                description = mutation["description"]
                references = [ref["source"]["id"] for ref in mutation["evidences"] if ref["source"]["name"] == "PubMed"]
                mut = {"type": type, "description": description, "start": start, "end": end, "alt": alt,
                       "pubmed_id": references, }
                mutations.append(mut)
        else:
            mutations = None

        return mutations
