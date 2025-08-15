import pandas as pd
import json

from ccm_benchmate.utils.general_utils import *


class UniProt:
    def __init__(self):
        """
        constructor for the UniProt class, which is used to gather data from the UniProt API. and process it in a readable format.
        :param uniprot_id:
        :param search_intact:
        :param consolidate_refs:
        :param kwargs:
        """
        self.url = "https://www.ebi.ac.uk/proteins/api/proteins?accession={}"
        self.headers = {'Accept': 'application/json'}


    def _gather(self, uniprot_id):
        """
        This function gathers data from the UniProt API using the provided uniprot_id.
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

    def search_uniprot(self, uniprot_id, consolidate_refs=True, get_variations=True,
                       get_interactions=True, get_mutagenesis=True, get_isoforms=True):
        """
        process the json response from the UniProt API and extract relevant information.
        :return: returns self because it modfies the class instance
        """
        id = uniprot_id
        json=self._gather(uniprot_id)
        sequence = json["sequence"]["sequence"]
        organism = {"name": json["organism"]['names'], "taxid": json["organism"]["taxonomy"]}

        gene = json['gene']
        feature_types = set([feat['type'] for feat in json["features"]])
        comment_types = set([feat["type"] for feat in json['comments']])
        references = self._extract_references(json)
        xref_types, xrefs = self._extract_xrefs(json)
        description = self._extract_description(json)
        name = json["protein"]['recommendedName']["fullName"]['value']
        results = {"id": id, "name": name, "sequence": sequence, "organism": organism, "gene": gene,
                   "feature_types": feature_types, "comment_types": comment_types, "references": references,
                   "xref_types": xref_types, "xrefs": xrefs, "description": description, "json": json,}

        if "secondaryAccession" in json.keys():
            secondary_accessions = [json["secondaryAccession"]]
            results["secondary_accessions"] = secondary_accessions

        if "alternativeNames" in json.keys():
            alternative_names = json['alternativeName']
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
            references = self.consolidate_references(results)
            results["references"] = references["references"]

        return results

    def _extract_description(self, results):
        """
        concanate the comments from the json response into a single string this can be used in nlp tasks or comparing
        uniprot instances
        :return:
        """
        desc = []
        for comment in results["comments"]:
            if "text" in comment.keys():
                desc.append("\n".join([item["value"] for item in comment["text"] if type(item)==dict]))
        description = "\n".join(desc)
        return description

    def _extract_references(self, results):
        """
        internal function to extract references from the json response
        :return: references
        """
        refs = []
        for reference in results["references"]:
            if "dbReferences" in reference["citation"].keys():
                for db in reference["citation"]["dbReferences"]:
                    if db["type"] in ["PubMed"]:
                        refs.append(db["id"])

        return refs

    def _extract_xrefs(self, results):
        """
        internal function to extract xrefs from the json response
        :return: xref types and xrefs
        """
        xrefs = results["dbReferences"]
        xref_types = list(set([item["type"] for item in xrefs]))
        xrefs = pd.DataFrame(xrefs)
        return xref_types, xrefs

    def get_features(self, results, feature_types=None):
        """
        filter already extracted features by type
        :param feature_types: type of the feature to filter by
        :return: the features
        """
        if feature_types is not None:
            features = [feat for feat in results["features"] if feat["type"] in feature_types]
        else:
            features = [feat for feat in results["features"]]
        return features

    def get_comments(self, results, types=None):
        """
        get already extracted comments from the json response
        :param types: comment types to filter by
        :return: comments
        """
        if types is not None:
            if type(types) == str:
                types = [types]
            comments = [comment for comment in results["comments"] if comment["type"] in types]
        else:
            comments = [feat for feat in results["comments"]]
        return comments

    def _get_variations(self, results):
        """
        query the uniprot API for variations
        :return: pandas DataFrame with the variations
        """
        url = 'https://www.ebi.ac.uk/proteins/api/variation?offset=0&size=-1&accession={}'
        variants = requests.get(url.format(results["id"]), headers=self.headers)
        warn_for_status(variants, "issues with getting variation")
        variants = json.loads(variants.content.decode())[0]
        variants = variants["features"]
        variants = pd.DataFrame(variants)
        variation = variants
        return variation

    def consolidate_references(self, results):
        """
        pul all references from the isoforms, mutagenesis, interactions and variations into a single list this is useful
        for literature mining and other tasks
        :return: references
        """

        if "isoforms" in results.keys() and results["isoforms"] is not None:
            for isoform in results["isoforms"]:
                for refs in isoform["pubmed_id"]:
                    results["references"].append(refs["pubmed_id"])

        if "mutagenesis" in results.keys() and results["mutagenesis"] is not None:
            for refs in results["mutagenesis"]["pubmed_id"].tolist():
                if refs is not None:
                    for ref in refs:
                        results["references"].append(ref)

        if "variation" in results.keys() and results["variation"] is not None \
                and "evidences" in results["variation"].columns:
            var_refs = results["variation"]["evidences"].dropna().tolist()
            for ref_list in var_refs:
                for ref in ref_list:
                    if ref["source"]["name"].lower() == "pubmed":
                        results["references"].append(ref["source"]["id"])

        results["references"]=list(set(results["references"]))
        return results



# TODO refactor to seprate intact
class Interactions:
    def __init__(self, uniprot):
        """
        constructor for the Interactions class, which is used to gather interaction data from the UniProt API as well as Intact database.
        :param uniprot:
        :param search_intact:
        :param kwargs:
        """
        self.uniprot_id = uniprot["id"]
        self.url = 'https://www.ebi.ac.uk/proteins/api/proteins/interaction/{}'
        self.headers = {'Accept': 'application/json'}
        self.gather()

    def gather(self):
        response = requests.get(self.url.format(self.uniprot_id), headers=self.headers)
        content = warn_for_status(response, "issues with gathering interaction data from intact")
        if content is not None:
            content = json.loads(content)
            content = pd.DataFrame(content[0]["interactions"])
        interactions = content
        return interactions

    # TODO need to move logic out of there for recursion need a __method__


class Isoforms:
    def __init__(self, uniprot):
        self.uniprot_id = uniprot["id"]
        self.url = 'https://www.ebi.ac.uk/proteins/api/proteins/{}/isoforms'
        self.headers = {'Accept': 'application/json'}
        self.gather()

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
                    reftypes = ref["citation"]
                    if "dbReferences" in reftypes.keys():
                        for rtype in reftypes:
                            if type(rtype) == dict:
                                if rtype["type"] == "Pubmed":
                                    ref_ids.append(type["id"])
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
            mutations = pd.DataFrame(mutations)
        else:
            mutations = None

        return mutations
