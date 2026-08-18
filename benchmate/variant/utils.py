
def infer_variant_type(ref_allele, alt_allele):
    """
    :param ref_allele: what the reference is
    :param alt_allele: what the alternative is
    :return Inferred variant type ('snv', 'deletion', 'insertion', 'indel', 'duplication', 'translocation')
    """
    if not ref_allele or not alt_allele:
        raise ValueError("Reference and alternative alleles must be provided")

    if "chr" in alt_allele and ":" in alt_allele:
        return "translocation"

    ref_len = len(ref_allele)
    alt_len = len(alt_allele)

    if ref_len == 1 and alt_len == 1 and ref_allele != alt_allele:
        return "snv"
    elif alt_len > ref_len and ref_allele in alt_allele and alt_allele.replace(ref_allele, "", 1) == ref_allele:
        return "duplication"
    elif ref_len < alt_len or (ref_len == 0 or ref_allele == "-"):
        return "insertion"
    elif ref_len > alt_len or (alt_len == 0 or alt_allele == "-"):
        return "deletion"
    elif ref_len > 1 and alt_len > 1 and ref_allele != alt_allele:
        return "indel"
    else:
        raise ValueError(f"Cannot infer variant type for ref: {ref_allele}, alt: {alt_allele}")


def to_hgvs(variant):
    """
    Convert genomic coordinates and variant details to HGVS notation, inferring variant type.
    :param variant, a type of variant instance
    :return hgvs, a HGVS notation
    """
    # Normalize chromosome format (remove 'chr' prefix if present)
    chrom = str(variant.chrom).replace('chr', '')

    ref = variant.ref or ""
    alt = variant.alt or ""
    pos = variant.pos

    # Infer variant type from original alleles
    variant_type = infer_variant_type(ref, alt)

    # Trim shared VCF anchor base if present
    if ref and alt and ref[0] == alt[0] and (len(ref) > 1 or len(alt) > 1):
        pos += 1
        ref = ref[1:]
        alt = alt[1:]

    # Handle variant types
    if variant_type == 'snv':
        hgvs = f"g.{pos}{ref}>{alt}"

    elif variant_type == 'deletion':
        end_pos = pos + len(ref) - 1
        if pos == end_pos:
            hgvs = f"g.{pos}del"
        else:
            hgvs = f"g.{pos}_{end_pos}del"

    elif variant_type == 'insertion':
        hgvs = f"g.{pos - 1}_{pos}ins{alt}"

    elif variant_type == 'duplication':
        end_pos = pos + len(ref) - 1
        if pos == end_pos:
            hgvs = f"g.{pos}dup"
        else:
            hgvs = f"g.{pos}_{end_pos}dup"

    elif variant_type == 'indel':
        end_pos = pos + len(ref) - 1
        if pos == end_pos:
            hgvs = f"g.{pos}delins{alt}"
        else:
            hgvs = f"g.{pos}_{end_pos}delins{alt}"

    elif variant_type == 'translocation':
        hgvs = f"g.{pos}t({alt})"

    else:
        raise ValueError(f"Unsupported inferred variant type: {variant_type}")

    # Prepend chromosome reference
    return f"chr{chrom}:{hgvs}"