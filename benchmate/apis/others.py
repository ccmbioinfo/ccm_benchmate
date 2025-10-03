# TODO this will include Gtex, Omnipath and not sure if this is needed)
import warnings
import time

import pandas as pd
import requests
import json

from alphagenome.models import dna_client, variant_scorers
from alphagenome.data import genome

from benchmate.variant.variant import SequenceVariant
from benchmate.ranges.genomicranges import GenomicRange
from benchmate.sequence.sequence import Sequence

from benchmate.apis.utils import api_call


class BioGrid:
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

    @api_call
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


class IntAct:
    def __init__(self, page=0, page_size=100):
        self.url = 'https://www.ebi.ac.uk/intact/ws/interaction/findInteractions/{}?page={}&pageSize={}'
        self.page = page
        self.page_size = page_size

    def _search(self, ebi_id, page):
        """
        Search for interactions in IntAct database.
        :param ebi_id: The EBI ID to search for.
        :return: A list of interactions.
        """

        intact_response = requests.get(self.url.format(ebi_id, page, self.page_size))
        intact_response.raise_for_status()
        intact_response = json.loads(intact_response.content.decode())
        interactions = []
        for ints in intact_response["content"]:
            interaction = {"idA": ints["idA"], "idB": ints["idB"], "taxidA": ints["taxIdA"], "taxidB": ints["taxIdB"],
                           "experimental_role_A": ints["experimentalRoleA"],
                           "experimental_role_B": ints["experimentalRoleB"], "stoichiometry_A": ints["stoichiometryA"],
                           "stoichiometry_B": ints["stoichiometryB"], "detection_method": ints["detectionMethod"],
                           "annotations": "\n".join(item for item in ints["allAnnotations"]),
                           "is_negative": ints["negative"], "affected_by_mutation": ints["affectedByMutation"],
                           "pubmed_id": ints["publicationPubmedIdentifier"], "score": ints["intactMiscore"], }

            interactions.append(interaction)
        if intact_response["last"]:
            last_page = True
        else:
            last_page = False

        return interactions, last_page

    @api_call
    def intact_search(self, ebi_id, page=0):
        interactions, last_page = self._search(ebi_id, page)
        while not last_page:
            page = page + 1
            next_page_interactions, last_page = self._search(ebi_id, page)
            interactions.extend(next_page_interactions)
        interactions = pd.DataFrame(interactions)
        return interactions

#TODO add mouse
class AlphaGenome:
    def __init__(self, access_key):
        """
        Create an AlphaGenome object. this is used to query the alhpagenome api, but unlike other api calls this does
        not return and api_call dataclass instance, instead it returns depending on the method, a variant, a genomic_range or
        a dataframe will be returned
        :param access_key: your alphagenome api key, you can get one from their website.
        """
        self.client = dna_client.create(access_key)
        self.output_types=[output.name for output in dna_client.OutputType]
        self.organisms=[org.name for org in dna_client.Organism]
        self.sequence_lengths=list(dna_client.SUPPORTED_SEQUENCE_LENGTHS.keys())
        self.scorers=variant_scorers.RECOMMENDED_VARIANT_SCORERS
        self.metadata={}
        for organism in self.organisms:
            self.metadata[organism]=self.client.output_metadata(dna_client.Organism[organism]).concatenate()
        self.ontologies={}
        for key in self.metadata.keys():
            self.ontologies[key]=self.metadata[key]["ontology_curie"].tolist()

    def predict_variant(self, variants, interval_size="SEQUENCE_LENGTH_2KB", organism="human"):
        """
        for a given list of variants predict their consequences, this does not mean you can pass a whole vcf file to it
        but you can do a few dozen at a time no problem.
        :param variants: list of variant objects, they do not need to have annotations
        :param interval_size: which interval should we consider, default 2KB
        :param organism: which organism should we consider, default human the other option is mouse, that's it.
        :return: a benchmate.Variant.SequenceVariant instances, the same ones passed to the function but with annotations
        """
        if organism == "human":
            org=dna_client.Organism.HOMO_SAPIENS
        if organism == "mouse":
            org=dna_client.Organism.MUS_MUSCULUS

        annotated_variants=[]
        for var in variants:
            if not isinstance(var, SequenceVariant):
                raise NotImplementedError("alphagenome can only process sequence variants")

            v=genome.Variant(var.chrom, var.pos, var.ref, var.alt)
            variant_output = self.client.score_variant(
                interval=dna_client.SUPPORTED_SEQUENCE_LENGTHS[interval_size],
                variant=v,
                organism=org,
                variant_scorers=list(variant_scorers.RECOMMENDED_VARIANT_SCORERS))
            variant_output=variant_scorers.tidy_scores(variant_output)
            var.add_annotations("alphagenome", variant_output)
            annotated_variants.append(var)
        return annotated_variants


    def predict_sequence(self, sequences, ontology_terms, interval_size="SEQUENCE_LENGTH_2KB", output_types=None, organism="human"):
        """
        predict features of a list of sequences, if you have only one you should pass [sequence] a
        :param sequences: list of benchmate.sequences.Sequence objects
        :param ontology_terms: which ontology terms to use if you do not specify any we'll use all of them
        :param interval_size: interval size to consider, default 2KB but if needs to be longer than your sequence
        :param output_types: see self.ouput_types or get them all (if none)
        :param organism: which organism to consider, default human the other option is mouse, that's it.
        :return: a list of benchmate.sequences.Sequence objects same ones with the features property filled in
        """
        if output_types is None:
            output_types=self.output_types

        for seq in sequences:
            if isinstance(seq, Sequence):
                raise ValueError("You can only pass sequence class instances")

        if organism == "human":
            org=dna_client.Organism.HOMO_SAPIENS
        if organism == "mouse":
            org=dna_client.Organism.MUS_MUSCULUS

        annotated_sequences=[]

        for seq in sequences:
            seq_len=len(seq.info.sequence)
            if self.sequence_lengths[interval_size] < seq_len:
                raise ValueError("Sequence length must be greater than sequence length")

            output=self.client.predict_sequence(
                seq=seq.center(interval_size, "N"),
                requested_outputs=output_types,
                ontology_terms=ontology_terms,
                organism=org,
            )

            attr_list = []
            for t in list(dna_client.OutputType):
                try:
                    attrs = output.__dict__[t.name.lower()]
                    df = attrs.metadata
                    tracks = attrs.values.T
                    df["tracks"] = tracks
                    attr_list.append(df)
                except:
                    warnings.warn("Attribute '{}' not found, skipping".format(t.name.lower()))

            attr_df = pd.concat(attr_list)
            seq.features["alphagenome"]=attr_df
            annotated_sequences.append(range)

        return annotated_sequences


    def predict_interval(self, granges, ontology_terms, interval_size="SEQUENCE_LENGTH_2KB", output_types=None, organism="human"):
        """
        predict things about an interval,
        :param granges: a list of granges or a grageges list object, if you have only one grange then pass it as a list [grange]
        :param ontology_terms: which ontology terms to use
        :param interval_size: interval size to consider, default 2KB, it needs to be longer then len(grange)
        :param output_types: see above
        :param organism: see above
        :return: a list of granges, with annotations
        """
        if output_types is None:
            output_types=self.output_types

        actual_terms=[]
        for term in ontology_terms:
            if term not in self.ontologies:
                warnings.warn("ontology term '{}' not found, skipping".format(term))
            else:
                actual_terms.append(term)

        if organism == "human":
            org=dna_client.Organism.HOMO_SAPIENS
        if organism == "mouse":
            org=dna_client.Organism.MUS_MUSCULUS

        annotated_intervals=[]
        for range in granges:
            if not isinstance(range, GenomicRange):
                raise ValueError("You need to pass either a GenomicRangesList or a list of GenomicRanges")
            if range.strand=="*":
                strand="."
            else:
                strand=range.strand

            if self.sequence_lengths[interval_size] < len(range):
                raise ValueError("Sequence length must be greater than sequence length")

            intv=genome.Interval(range.chrom, range.start, range.end, strand)
            intv=intv.resize(dna_client.SUPPORTED_SEQUENCE_LENGTHS[interval_size])
            output=self.client.predict_interval(intv, requested_outputs=output_types,
                                                ontology_terms=actual_terms, organism=org)
            attr_list=[]
            for t in list(dna_client.OutputType):
                try:
                    attrs=output.__dict__[t.name.lower()]
                    df=attrs.metadata
                    tracks=attrs.values.T
                    df["tracks"]=tracks
                    attr_list.append(df)
                except:
                    warnings.warn("Attribute '{}' not found, skipping".format(t.name.lower()))

            attr_df=pd.concat(attr_list)
            range.add_annotation("alphagenome", attr_df)
            annotated_intervals.append(range)

        return annotated_intervals


    def mutagenesis(self, granges, scorers, mutagenesis_region=None ,interval_size="SEQUENCE_LENGTH_2KB",
                    output_types=None, organism="human"):
        """
        Perform in-silico mutagenesis for all the sequences in the range you provided
        :param granges: list of granges
        :param scorers: list of scorers, see self.scorers
        :param interval_size: which interval size to consider, default 2KB, it needs to be longer then len(grange)
        :param mutagenesis_region: which region of the sequence to mutate extensively, this needs to be shorter than your
        interval size, the method picks the center of the rage and mutagenesis_region/2 on each side
        :return: a dataframe of scores or a list of dataframe of scores if you picked more than one scorer, if you get
        greedy and ask for all the things the server might kick you out.
        """

        if output_types is None:
            output_types=self.output_types

        if organism == "human":
            org = dna_client.Organism.HOMO_SAPIENS
        if organism == "mouse":
            org = dna_client.Organism.MUS_MUSCULUS


        mutagenesis_outputs=[]

        for range in granges:
            if not isinstance(range, GenomicRange):
                raise ValueError("ranges must be instances of GenomicRanges object")

            intv = genome.Interval(range.chrom, range.ranges.start, range.ranges.end)
            intv=intv.resize(dna_client.SUPPORTED_SEQUENCE_LENGTHS[interval_size])

            if mutagenesis_region is None:
                mutagenesis_region=len(range)

            ism_interval=intv.resize(mutagenesis_region)

            scores={}
            for scorer in scorers:
                func=self.scorers[scorer]
                variant_scores = self.client.score_ism_variants(
                    interval=intv,
                    ism_interval=ism_interval,
                    variant_scorers=func,
                    organism=org,
                )

                score_array=[]
                for v in variant_scores:
                    score_array.append(v[0].to_df())

                score_array=pd.concat(score_array)
                scores[scorer] = score_array

            mutagenesis_outputs.append(scores)

        return mutagenesis_outputs











