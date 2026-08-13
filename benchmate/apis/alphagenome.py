import warnings

import pandas as pd

from alphagenome.models import dna_client, variant_scorers
from alphagenome.data import genome

from benchmate.variant.variant import SequenceVariant
from benchmate.ranges.genomicranges import GenomicRange
from benchmate.sequence.sequence import Sequence

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
            org = dna_client.Organism.HOMO_SAPIENS
        elif organism == "mouse":
            org = dna_client.Organism.MUS_MUSCULUS
        else:
            raise ValueError(f"Organism {organism} not supported. Must be 'human' or 'mouse'.")

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
            if not isinstance(seq, Sequence):
                raise ValueError("You can only pass sequence class instances")

        if organism == "human":
            org = dna_client.Organism.HOMO_SAPIENS
        elif organism == "mouse":
            org = dna_client.Organism.MUS_MUSCULUS
        else:
            raise ValueError(f"Organism {organism} not supported. Must be 'human' or 'mouse'.")

        target_len = dna_client.SUPPORTED_SEQUENCE_LENGTHS[interval_size]
        annotated_sequences=[]

        for seq in sequences:
            raw_seq = seq.info.sequence
            seq_len = len(raw_seq)
            if target_len < seq_len:
                raise ValueError(f"Sequence length ({seq_len}) must be less than or equal to target interval length ({target_len})")

            # Center pad sequence to target_len with 'N'
            pad_needed = target_len - seq_len
            pad_left = pad_needed // 2
            pad_right = pad_needed - pad_left
            centered_seq = ("N" * pad_left) + raw_seq + ("N" * pad_right)

            output=self.client.predict_sequence(
                seq=centered_seq,
                requested_outputs=output_types,
                ontology_terms=ontology_terms,
                organism=org,
            )

            attr_list = []
            for t in list(dna_client.OutputType):
                try:
                    attrs = output.__dict__.get(t.name.lower())
                    if attrs is not None:
                        df = attrs.metadata.copy()
                        tracks = attrs.values.T
                        df["tracks"] = tracks.tolist() if hasattr(tracks, 'tolist') else list(tracks)
                        attr_list.append(df)
                except Exception as e:
                    warnings.warn(f"Attribute '{t.name.lower()}' failed: {e}")

            attr_df = pd.concat(attr_list, ignore_index=True) if attr_list else pd.DataFrame()
            seq.annotations["alphagenome"] = attr_df
            annotated_sequences.append(seq)

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

        all_ontologies = set()
        for term_list in self.ontologies.values():
            if isinstance(term_list, (list, set)):
                all_ontologies.update(term_list)

        actual_terms=[]
        for term in (ontology_terms or []):
            if term not in all_ontologies:
                warnings.warn("ontology term '{}' not found, skipping".format(term))
            else:
                actual_terms.append(term)

        if organism == "human":
            org = dna_client.Organism.HOMO_SAPIENS
        elif organism == "mouse":
            org = dna_client.Organism.MUS_MUSCULUS
        else:
            raise ValueError(f"Organism {organism} not supported. Must be 'human' or 'mouse'.")

        target_len = dna_client.SUPPORTED_SEQUENCE_LENGTHS[interval_size]
        annotated_intervals=[]
        for grange in granges:
            if not isinstance(grange, GenomicRange):
                raise ValueError("You need to pass either a GenomicRangesList or a list of GenomicRanges")
            if grange.strand=="*":
                strand="."
            else:
                strand=grange.strand

            if target_len < len(grange):
                raise ValueError(f"Interval length ({len(grange)}) must be less than or equal to target interval size ({target_len})")

            intv=genome.Interval(grange.chrom, grange.ranges.start, grange.ranges.end, strand)
            intv=intv.resize(target_len)
            output=self.client.predict_interval(intv, requested_outputs=output_types,
                                                ontology_terms=actual_terms, organism=org)
            attr_list=[]
            for t in list(dna_client.OutputType):
                try:
                    attrs = output.__dict__.get(t.name.lower())
                    if attrs is not None:
                        df = attrs.metadata.copy()
                        tracks = attrs.values.T
                        df["tracks"] = tracks.tolist() if hasattr(tracks, 'tolist') else list(tracks)
                        attr_list.append(df)
                except Exception as e:
                    warnings.warn(f"Attribute '{t.name.lower()}' failed: {e}")

            attr_df = pd.concat(attr_list, ignore_index=True) if attr_list else pd.DataFrame()
            grange.add_annotation("alphagenome", attr_df)
            annotated_intervals.append(grange)

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
        elif organism == "mouse":
            org = dna_client.Organism.MUS_MUSCULUS
        else:
            raise ValueError(f"Organism {organism} not supported. Must be 'human' or 'mouse'.")

        target_len = dna_client.SUPPORTED_SEQUENCE_LENGTHS[interval_size]
        mutagenesis_outputs=[]

        for grange in granges:
            if not isinstance(grange, GenomicRange):
                raise ValueError("ranges must be instances of GenomicRanges object")

            intv = genome.Interval(grange.chrom, grange.ranges.start, grange.ranges.end)
            intv=intv.resize(target_len)

            cur_mutagenesis_region = len(grange) if mutagenesis_region is None else mutagenesis_region
            ism_interval=intv.resize(cur_mutagenesis_region)

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

                score_array=pd.concat(score_array, ignore_index=True) if score_array else pd.DataFrame()
                scores[scorer] = score_array

            mutagenesis_outputs.append(scores)

        return mutagenesis_outputs