
from Bio.PDB import *
import requests

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
    if source == "PDB":
        url = "http://files.rcsb.org/download/{}.cif".format(id)
    elif source == "AFDB":
        url = "https://alphafold.ebi.ac.uk/files/AF-{}-F1-model_v4.pdb".format(id)
    else:
        raise NotImplementedError("We can only download structures from PDB or AFDB")

    download = requests.get(url, stream=True)
    download.raise_for_status()
    with open("{}/{}.pdb".format(destination, id), "wb") as f:
        f.write(download.content)

    return destination


def get_pocket_dimensions(pocket_path):
    """
    Args:
        pocket_path (str): Path to the PDB file of the binding pocket.

    Returns:
        tuple:
            center (list of float): The [x, y, z] center coordinates.
            bbox_size (float): The maximum length in any dimension.
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

# need to figure out where to put this
def bounding_box(self, amino_acids=None, use_alpha_carbon=False):
        """
        generate a bounding box around a given list of amino acid ids. This can be used to generate more molecules or
        calculate properties of a pocket
        :param use: target or bound structure, this needs to be a Structure instance
        :param amino_acids: which amino acids to use
        :param use_alpha_carbon: whether to use the alpha carbon or the side chains to get the bounding box
        :return: 6 coordinates of the bounding box
        """

        if self.bound_structure is None:
            raise ValueError("bound_sturcutre must be set for bounding box calculation")

        coord = []

        for model in self.bound_structure:
            for chain in model:
                for residue in chain:
                    if amino_acids is None or residue.resname in amino_acids:
                        for atom in residue:
                            if use_alpha_carbon:
                                if atom.name == "CA":
                                    coord.append(atom.coord)
                            else:
                                coord.append(atom.coord)

        coord_numpy = np.array(coord)

        x_max, y_max, z_max = np.max(coord_numpy, axis=0)
        x_min, y_min, z_min = np.min(coord_numpy, axis=0)

        return {"xmax": x_max, "ymax": y_max, "zmax": z_max, "xmin": x_min, "ymin": y_min, "zmin": z_min}

