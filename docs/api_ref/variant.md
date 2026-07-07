---
layout: default
title: Variant
parent: API Reference
nav_order: 10
---

<a id="benchmate.variant"></a>

# benchmate.variant

<a id="benchmate.variant.variant"></a>

# benchmate.variant.variant

<a id="benchmate.variant.variant.BaseVariant"></a>

## BaseVariant Objects

```python
@dataclass(slots=True)
class BaseVariant()
```

base variant class to be subclassed below, contains the bare minimun information of a variant

<a id="benchmate.variant.variant.BaseVariant.show_annotations"></a>

#### show\_annotations

```python
def show_annotations() -> Dict[str, Any]
```

Return annotation types.

<a id="benchmate.variant.variant.BaseVariant.query_annotation"></a>

#### query\_annotation

```python
def query_annotation(key: str) -> Any
```

Query a specific annotation.

<a id="benchmate.variant.variant.BaseVariant.add_annotation"></a>

#### add\_annotation

```python
def add_annotation(key: str, value: Any) -> None
```

Add or update an annotation.

<a id="benchmate.variant.variant.SequenceVariant"></a>

## SequenceVariant Objects

```python
@dataclass(slots=True)
class SequenceVariant(BaseVariant)
```

simple sequence variation, snps, small dels, ins and indels

<a id="benchmate.variant.variant.SequenceVariant.__len__"></a>

#### \_\_len\_\_

```python
def __len__()
```

Return the length of the variant.

<a id="benchmate.variant.variant.SequenceVariant.__str__"></a>

#### \_\_str\_\_

```python
def __str__()
```

Return a string representation of the variant.

<a id="benchmate.variant.variant.SequenceVariant.__repr__"></a>

#### \_\_repr\_\_

```python
def __repr__()
```

Return a detailed string representation of the variant.

<a id="benchmate.variant.variant.StructuralVariant"></a>

## StructuralVariant Objects

```python
@dataclass(slots=True)
class StructuralVariant(BaseVariant)
```

larger variations including translocation or transversions

<a id="benchmate.variant.variant.StructuralVariant.svlen"></a>

#### svlen

length of the sv

<a id="benchmate.variant.variant.StructuralVariant.__len__"></a>

#### \_\_len\_\_

```python
def __len__()
```

Return the length of the variant.

<a id="benchmate.variant.variant.StructuralVariant.reciprocal_overlap"></a>

#### reciprocal\_overlap

```python
def reciprocal_overlap(other)
```

find overlaps between variants

**Arguments**:

- `other`: other StructuralVariant

**Returns**:

fraction overlap

<a id="benchmate.variant.variant.StructuralVariant.__str__"></a>

#### \_\_str\_\_

```python
def __str__()
```

Return a string representation of the variant.

<a id="benchmate.variant.variant.StructuralVariant.__repr__"></a>

#### \_\_repr\_\_

```python
def __repr__()
```

Return a detailed string representation of the variant.

<a id="benchmate.variant.variant.TandemRepeatVariant"></a>

## TandemRepeatVariant Objects

```python
@dataclass(slots=True)
class TandemRepeatVariant(BaseVariant)
```

Class for Tandem Repeat variants (SRWGS and LRWGS).

<a id="benchmate.variant.variant.TandemRepeatVariant.__len__"></a>

#### \_\_len\_\_

```python
def __len__()
```

Return the length of the variant.

<a id="benchmate.variant.variant.TandemRepeatVariant.__str__"></a>

#### \_\_str\_\_

```python
def __str__()
```

Return a string representation of the variant.

<a id="benchmate.variant.variant.TandemRepeatVariant.__repr__"></a>

#### \_\_repr\_\_

```python
def __repr__()
```

Return a detailed string representation of the variant.

<a id="benchmate.variant.utils"></a>

# benchmate.variant.utils

<a id="benchmate.variant.utils.infer_variant_type"></a>

#### infer\_variant\_type

```python
def infer_variant_type(ref_allele, alt_allele)
```

:param ref_allele: what the reference is

:param alt_allele: what the alternative is
:return Inferred variant type ('snv', 'deletion', 'insertion', 'indel', 'duplication', 'translocation')


<a id="benchmate.variant.utils.to_hgvs"></a>

#### to\_hgvs

```python
def to_hgvs(variant)
```

Convert genomic coordinates and variant details to HGVS notation, inferring variant type.

:param variant, a type of variant instance
:return hgvs, a HGVS notation


