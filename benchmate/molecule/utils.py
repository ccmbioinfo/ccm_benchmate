import numpy as np

# The usearch intergration is suspended for now.
# from usearch_molecules.dataset import FingerprintedDataset, shape_ecfp4, shape_fcfp4, shape_maccs
# from usearch_molecules.raw_dataset import *
#
# def generate_molecule_dataset(smiles_files, library_dir, shapes=[shape_maccs, shape_ecfp4, shape_fcfp4],
#                               extractor=None, processes=10):
#     """
#     generates a usearch-molecules dataset from a list of molecules and associated fingerprints
#     along with indicies
#     :param molecules: list of molecule objects
#     :param path: where to write the dataset
#     :return:
#     """
#     print("generating molecules dataset")
#     rd=RawDataset(smiles_files, library_dir, extractor=extractor)
#     rd.prep_shards()
#     print("preparing shards")
#     rd.export_shards()
#     print(f"preparing fingerprints with {processes} processes")
#     augment_parquet_shards(rd, processes=processes)
#
#     print(f"creating indices for {','.join([shape.name for shape in shapes])}")
#     fp=FingerprintedDataset(library_dir, shapes)
#     fp.index()
#     print(f"molecule library is ready for searching under {library_dir}")


def tanimoto(a, b):
    if a is None or b is None:
        return 0.0
    ands = np.logical_and(a, b).sum()
    ors = np.logical_or(a, b).sum()
    if ors == 0:
        return 0.0
    return ands / ors