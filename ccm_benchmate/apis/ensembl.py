import warnings

import pandas as pd
import requests
import json

from ccm_benchmate.ranges.genomicranges import GenomicRange
from ccm_benchmate.variant.variant import *

#I'm skipping the genome stuff because we have the genome class that will get the genome build the db etc.
# this is also the whole point of genomic ranges classes, that we can do these calculations locally, I do not think
# user will be using more than a few genomes at any given time so there is no reason for api calls
class Ensembl:
    """
    Ensembl API wrapper for the Ensembl REST API.
    """
    def __init__(self):
        """
        Initialize the Ensembl API wrapper. there are some basic variables that are set there is nothing here for the user to
        set. The base url is the ensembl rest api url, the dataset is the dataset that will be used for the queries, and the
        headers are the headers that will be used for the queries.
        """
        self.base_url = "https://rest.ensembl.org"
        self.dataset = "hsapiens_gene_ensembl"
        self.headers={ "Content-Type" : "application/json"}
        self.vep_tools = ['AlphaMissense', 'AncestralAllele', 'Blosum62', 'CADD', 'Conservation', 'DisGeNET',
                          'DosageSensitivity', 'EVE', 'Enformer', 'GO', 'GeneSplicer', 'Geno2MP', 'IntAct', 'LoF',
                          'Mastermind', 'MaveDB', 'MaxEntScan', 'NMD', 'OpenTargets', 'Phenotypes', 'SpliceAI',
                          'UTRAnnotator', 'appris', 'canonical', 'ccds', 'dbNSFP', 'dbscSNV',
                          'distance', 'domains', 'failed', 'flag_pick', 'flag_pick_allele', 'flag_pick_allele_gene',
                          'ga4gh_vrs', 'gencode_basic', 'hgvs', 'mane', 'merged', 'minimal', 'mirna', 'mutfunc',
                          'numbers', 'per_gene', 'pick', 'pick_allele', 'pick_allele_gene', 'protein',
                          'refseq', 'shift_3prime', 'shift_genomic', 'transcript_version',
                          'tsl', 'uniprot', 'variant_class', 'vcf_string', 'xref_refseq']

    def variation(self,  id, method=None, species="human", pubtype=None, add_annotations=False):
        """
        Get variation information from the Ensembl REST API.
        :param id:
        :param method: search method, default is None which means we will get information otherwise you can search for
        publications (pmid and pmcid) or translation which converts the notations to other notations
        :param species: species to search for, default is human
        :param pubtype:
        :return:
        """
        methods=["translate", "publication"]
        if method not in methods and method is not None:
            raise NotImplementedError("Method {} not implemented".format(method))
        elif method is None:
            ext = f"/variation/{species}/{id}"
            if add_annotations:
                ext = f"{ext}?genotypes=1;phenotypes=1;pops=1;population_genotypes=1"
        else:
            if method == "translate":
                ext = f"/variant_recoder/{species}/{id}?"
            elif method == "publication":
                if pubtype=="pubmed":
                    ext = f"/variation/human/pmid/{id}?"
                elif pubtype=="pmc":
                    ext = f"/variation/human/pmcid/{id}?"
                else:
                    raise ValueError("pubtype must be one of ['pubmed', 'pmc']")
        response= requests.get(f"{self.base_url}{ext}", headers=self.headers)
        response.raise_for_status()
        decoded = json.loads(response.text)
        return decoded


    def vep(self, species, variant, tools, check_existing=True):
        """"
        Get variant effect prediction from the Ensembl REST API.
        :param species: species to search for
        :param variant: variant to search for, must be a Variant object
        :param tools: tools to use for the prediction, default is None which means we will just return basic information
        :param check_existing: check population frequencies from gnomad and 1kg
        :return: variant effect prediction a detailed dict
        """
        var_string=to_hgvs(variant)
        ext= f"/vep/{species}/hgvs/{var_string}?"
        if tools is not None:
            for i in range(len(tools)):
                if tools[i] not in self.vep_tools:
                    warnings.warn(f"Tool {tools[i]} not available in VEP api")
                else:
                    if i > 0:
                        ext = f"{ext};{tools[i]}={1}"
                    else:
                        ext = f"{ext}{tools[i]}={1}"
        if check_existing:
            ext = f"{ext};?check_existing=1&af=1&af_1kg=1&af_gnomad=1"
        response = requests.get(f"{self.base_url}{ext}", headers=self.headers)
        response.raise_for_status()
        decoded = json.loads(response.text)
        decoded = decoded[0]
        return decoded

    def phenotype(self, grange, species="human"):
        """
        Get phenotype information from the Ensembl REST API that is associated with the genomic range.
        :param grange: a GenomicRange object
        :param species: species to search for, default is human
        :return: a dictionary with the phenotype information
        """
        if not isinstance(grange, GenomicRange):
            raise ValueError("grange must be a GenomicRange object")

        ext= f"/phenotype/region/{species}/{grange.chrom}:{grange.ranges.start}-{grange.ranges.end}"
        response = requests.get(f"{self.base_url}{ext}?include_pubmed_id=1", headers=self.headers)
        response.raise_for_status()
        decoded = json.loads(response.text)
        return decoded

    def sequence(self, id, trim_end=None, trim_start=None, expand_3=None, expand_5=None, sequence_type="genomic"):
        """
        Get sequence information from the Ensembl REST API for a given ensembl id
        :param id: ensembl id, because the ids also specify the species you do not need to specify the species
        :param trim_end: trim this many nucleotides from the end
        :param trim_start: trim this many nucleotides from the start
        :param expand_3: expand this many nucleotides from the 3' end not compatible with trim_end
        :param expand_5: expand this many nucleotides from the 5' end not compatible with trim_start
        :param sequence_type: genomics, cds, protein, cdna
        :return:
        """
        types=["genomic", "cds", "protein", "cdna"]
        if trim_end is not None and expand_3 is not None:
            raise ValueError("trim_end and trim_start are mutually exclusive")
        elif trim_start is not None and expand_5 is not None:
            raise ValueError("trim_start and expand_5 are mutually exclusive")
        else:
            ext = f"/sequence/id/{id}"

        if sequence_type not in types:
            raise ValueError("sequence_type must be one of ['genomic', 'cds', 'protein', 'cdna']")

        ext=f"{ext}?type={sequence_type};multiple_sequences=1"
        response = requests.get(f"{self.base_url}{ext}", headers=self.headers)
        response.raise_for_status()
        decoded = pd.DataFrame(response.json())
        return decoded


    def xrefs(self, id):
        """
        Get cross references from the Ensembl REST API for a given ensembl id
        :param id: ensembl id, because the ids also specify the species you do not need to specify the species
        :return: a dict of cross references these can be used to get the ids from other databases from other apis
        """
        ext = f"/xrefs/id/{id}?all_levels=1"
        response = requests.get(f"{self.base_url}{ext}", headers=self.headers)
        response.raise_for_status()
        decoded=pd.DataFrame(response.json())
        return decoded

    def mapping(self, id, start, end, type="cDNA"):
        """
        Get mapping information from the Ensembl REST API for a given ensembl id, convert between cDNA, CDS and protein
        :param id: ensembl id, because the ids also specify the species you do not need to specify the species
        :param start: start position of the range
        :param end: end position of the range
        :param type: type of mapping, cDNA, CDS or protein
        :return: dict of mapping information, this not really compatible with genomicranges that's why the inputs are different
        """
        if type == "cDNA":
            ext = f"/map/cdna/{id}/{start}..{end}"
        elif type == "CDS":
            ext = f"/map/cds/{id}/{start}..{end}"
        elif type == "protein":
            ext = f"/map/translation/{id}/{start}..{end}"
        else:
            raise ValueError("type must be one of ['cDNA', 'CDS', 'protein']")

        response = requests.get(f"{self.base_url}{ext}", headers=self.headers)
        response.raise_for_status()
        decoded = json.loads(response.text)
        return decoded

    def overlap(self, grange, features=None, species="human"):
        """
        Get overlap information from the Ensembl REST API for a given genomic range, this can be used to get the features that are
        within a region of interest. The features can be specified as a list of strings, if no features are specified all features will be returned.
        :param grange: a GenomicRange object
        :param features: features to get, default is None which means all features will be returned
        :param species: species to search for, default is human
        :return: a dict of overlap information, this is a dict of dicts where the keys are the features and the values are the genomic features
        """
        available_features= ["band", "gene", "transcript", "cds", "exon", "repeat", "simple", "misc", "variation", "somatic_variation",
                       "structural_variation", "somatic_structural_variation", "constrained", "regulatory", "motif", "mane"]
        features_to_use=[]
        if features is None:
            features_to_use=available_features
        else:
            for feature in features:
                if feature not in available_features:
                    warnings.warn(f"Feature {feature} not available")
                    continue
                else:
                    features_to_use.append(feature)


        if not isinstance(grange, GenomicRange):
            raise ValueError("grange must be a GenomicRange object")

        initial_ext = f"/overlap/region/{species}/{grange.chrom}:{grange.ranges.start}-{grange.ranges.end}?"
        for i in range(len(features_to_use)):
            if i==0:
                ext=initial_ext
                ext=f"{ext}feature={features_to_use[i]}"
            else:
                ext=f"{ext};feature={features_to_use[i]}"

        response = requests.get(f"{self.base_url}{ext}", headers=self.headers)
        response.raise_for_status()
        decoded = json.loads(response.text)
        return decoded

    def info(self):
        """
        Get information from the Ensembl REST API, this returns general information about the api,
        used to get an idea of what is available in the api.
        :return: divisions, species and consequences that are available in the api
        """
        # this is going to ge, species, consequence types
        divisions = "https://rest.ensembl.org/info/divisions?"
        species = "https://rest.ensembl.org/info/species"
        consequences = "https://rest.ensembl.org/info/variation/consequence_types?"

        divisions=requests.get(divisions, headers=self.headers)
        divisions=json.loads(divisions.text)

        species=requests.get(species, headers=self.headers)
        species=json.loads(species.text)

        consequences=requests.get(consequences, headers=self.headers)
        consequences=json.loads(consequences.text)

        data={"divisions": divisions,
              "species": species,
              "consequences": consequences}
        return data

    def show_vep_tools(self):
        return self.vep_tools


    #TODO haplotypes?



