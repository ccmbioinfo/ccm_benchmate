
from Bio.PDB import *
import requests
import numpy as np

THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    # common ambiguous / nonstandard entries can map to X
    "MSE": "M",  # selenomethionine -> treat as M
}


pdb_parser = PDBParser(PERMISSIVE=1)
cif_parser = MMCIFParser()


def download(id, source="PDB", destination=None):
    """
    download a cif file (RSCB) or a pdb file (AFDB) for a given id
    :param id: id
    :param source: where to get it from PDB or AFDB
    :param destination: where to download ti
    :return:  a path, you can use this to download things it's also being used by Structure internally
    """
    if source == "PDB":
        url = "http://files.rcsb.org/download/{}.cif".format(id)
        format="cif"
    elif source == "AFDB":
        url = "https://alphafold.ebi.ac.uk/files/AF-{}-F1-model_v6.pdb".format(id)
        format="pdb"
    else:
        raise NotImplementedError("We can only download structures from PDB or AFDB")

    download = requests.get(url, stream=True)
    download.raise_for_status()
    with open("{}/{}.{}".format(destination, id, format), "wb") as f:
        f.write(download.content)

    return "{}/{}.{}".format(destination, id, format)


def get_pocket_dimensions(pocket_path):
    """
    get the bounding box of a pocket
    :param pocket_path: pocket pdb from find_pockets
    :return: x,y,z coords
    """
    parser = PDBParser(PERMISSIVE=1)
    structure = parser.get_structure("pocket", pocket_path)

    coord = []

    # Extract all atom coordinates from the pocket structure
    for model in structure:
        for chain in model:
            for residue in chain:
                for atom in residue:
                    coord.append(atom.coord)

    # Convert list of coordinates to NumPy array
    coord_numpy = np.array(coord)

    # Find max and min along each axis
    x_max, y_max, z_max = np.max(coord_numpy, axis=0)
    x_min, y_min, z_min = np.min(coord_numpy, axis=0)

    # Compute the size of the bounding box (max extent)
    bbox_size = max(x_max - x_min, y_max - y_min, z_max - z_min)

    # Compute the geometric center of the pocket
    center = [
        (x_max + x_min) / 2,
        (y_max + y_min) / 2,
        (z_max + z_min) / 2
    ]
    return center, bbox_size

def bounding_box(structure, amino_acids=None, use_alpha_carbon=False):
    """
    generate a bounding box around a given list of amino acid ids/names or full structure.
    :param structure: Structure or Biotite/Bio.PDB structure
    :param amino_acids: which amino acids to use
    :param use_alpha_carbon: whether to use the alpha carbon or side chains
    :return: dict of bounding box coordinates
    """
    target = getattr(structure, "info", structure)
    atoms = getattr(target, "atoms", target)

    coord = []
    if hasattr(atoms, "coord"):
        # Biotite AtomArray
        for atom in atoms:
            if amino_acids is not None and atom.res_name not in amino_acids:
                continue
            if use_alpha_carbon and atom.atom_name != "CA":
                continue
            coord.append(atom.coord)
    else:
        # Bio.PDB structure
        for model in atoms:
            for chain in model:
                for residue in chain:
                    if amino_acids is None or residue.resname in amino_acids:
                        for atom in residue:
                            if use_alpha_carbon and atom.name != "CA":
                                continue
                            coord.append(atom.coord)

    if len(coord) == 0:
        raise ValueError("No matching atoms found for bounding box calculation")

    coord_numpy = np.array(coord)
    x_max, y_max, z_max = np.max(coord_numpy, axis=0)
    x_min, y_min, z_min = np.min(coord_numpy, axis=0)

    return {"xmax": float(x_max), "ymax": float(y_max), "zmax": float(z_max),
            "xmin": float(x_min), "ymin": float(y_min), "zmin": float(z_min)}

