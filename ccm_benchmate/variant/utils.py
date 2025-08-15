from ccm_benchmate.variant.variant import *

def infer_variant_type(ref_allele, alt_allele):
    """
    Infer the variant type based on reference and alternative alleles.

    Args:
        ref_allele (str): Reference allele sequence
        alt_allele (str): Alternative allele sequence

    Returns:
        str: Inferred variant type ('snv', 'deletion', 'insertion', 'indel', 'duplication', 'translocation')
    """
    if not ref_allele or not alt_allele:
        raise ValueError("Reference and alternative alleles must be provided")

    ref_len = len(ref_allele)
    alt_len = len(alt_allele)

    if ref_len == 1 and alt_len == 1 and ref_allele != alt_allele:
        return "snv"
    elif ref_len < alt_len or (ref_len == 0 or ref_allele == "-"):
        return "insertion"
    elif ref_len > alt_len or (alt_len == 0 or alt_allele == "-"):
        return "deletion"
    elif ref_len > 1 and alt_len > 1 and ref_allele != alt_allele:
        # Check for translocation pattern (e.g., "chr7:800" in alt_allele)
        if "chr" in alt_allele and ":" in alt_allele:
            return "translocation"
        return "indel"
    elif alt_len > ref_len and ref_allele in alt_allele and alt_allele.replace(ref_allele, "", 1) == ref_allele:
        return "duplication"
    else:
        raise ValueError(f"Cannot infer variant type for ref: {ref_allele}, alt: {alt_allele}")


def to_hgvs(variant):
    """
    Convert genomic coordinates and variant details to HGVS notation, inferring variant type.

    Args:
        chromosome (str): Chromosome name (e.g., '1', 'X', 'chr1')
        position (int): Genomic position of the variant
        ref_allele (str): Reference allele or sequence
        alt_allele (str): Alternative allele or sequence

    Returns:
        str: HGVS notation for the variant
    """
    # Normalize chromosome format (remove 'chr' prefix if present)
    chrom = str(variant.chrom).replace('chr', '')

    # Infer variant type
    variant_type = infer_variant_type(variant.ref, variant.alt)

    # Initialize HGVS prefix (genomic level, 'g.' for genomic)
    hgvs = f"g.{variant.pos}"

    # Handle variant types
    if variant_type == 'snv':
        hgvs += f"{variant.ref}>{variant.alt}"

    elif variant_type == 'deletion':
        if variant.pos + len(variant.ref) - 1 == variant.pos:
            hgvs += "del"
        else:
            hgvs += f"_{variant.pos + len(variant.ref) - 1}del"

    elif variant_type == 'insertion':
        hgvs += f"_{variant.pos + 1}ins{variant.alt}"

    elif variant_type == 'duplication':
        if variant.pos + len(variant.ref) - 1 == variant.pos:
            hgvs += "dup"
        else:
            hgvs += f"_{variant.pos + len(variant.ref) - 1}dup"

    elif variant_type == 'indel':
        end_pos = variant.pos + len(variant.ref) - 1
        hgvs += f"_{end_pos}delins{variant.alt}"

    elif variant_type == 'translocation':
        # Translocations are complex; simplified notation with alt_allele as breakpoint
        hgvs += f"t({variant.alt})"

    else:
        raise ValueError(f"Unsupported inferred variant type: {variant_type}")

    # Prepend chromosome reference
    return f"chr{chrom}:{hgvs}"