import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List, Union, Tuple, Optional


import biotite
from biotite.structure import distance, get_chains, alphabet, to_sequence, filter_amino_acids
from biotite.structure.io.pdb import PDBFile
from biotite.structure.io.pdbx import CIFFile, get_structure

from benchmate.structure.utils import *
from benchmate.sequence.sequence import Sequence, SequenceList




def _read(file):
    """
    read a pdb or cif file
    :param file: path to file
    :return: atom array
    """
    if file.endswith(".pdb"):
        structure = PDBFile.read(file).get_structure()[0]
    elif file.endswith(".cif") or file.endswith(".mmcif"):
        file = CIFFile.read(file)
        structure = get_structure(file, model=1)
    else:
        raise NotImplementedError("We can only read PDB or CIF files")
    return structure

@dataclass(slots=True)
class StructureInfo:
    name: str
    atoms: biotite.structure.AtomArray
    chains: List
    annotations: Optional[dict] = None

class Structure:
    def __init__(self, name, atoms, annotations:dict=None):
        """
        :param name: name
        :param atoms: a biotite.AtomArray
        :param annotations: a dict with annotations
        """
        chains = get_chains(atoms)
        self.name=name
        self.info=StructureInfo(name, atoms, chains, annotations)

    def align(self, other):
        """
        align 2 structures using mustang
        :param other:  other structure
        :param destination: where to save the output
        :return: aligned structure as a Structure class and other supplementary file paths
        """
        assert(isinstance(other, Structure))

        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, f"{self.name}.pdb")
            f2 = os.path.join(tmpdir, f"{other.name}.pdb")

            self.write(f1)
            other.write(f2)


            command = ["mustang", "-i", f1, f2, "-o", os.path.join(tmpdir, "results")]
            process = subprocess.run(command, capture_output=True, text=True)
            if process.returncode != 0:
                raise ValueError("There was an error aligning structures. See error below \n {}".format(process.stderr))
            aligned_s = Structure.from_file(f"{self.name}_{other.name}_aligned", os.path.join(tmpdir, "results.pdb"))
            return aligned_s

    def find_pockets(self, **kwargs):
        """
        Run fpocket on this structure and return detected pocket info.
        Returns (pocket_files, pocket_coords)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, f"{self.name}.pdb")
            self.write(f1)

            command = ["fpocket", "-f", f1, "-x", "-d"]
            for k, v in kwargs.items():
                command.extend([f"--{k}", str(v)])
            run = subprocess.run(command, capture_output=True, text=True)

            if run.returncode != 0:
                raise RuntimeError(run.stderr)
            out_dir = os.path.join(tmpdir, f"{self.name}_out")
            if not os.path.exists(out_dir):
                return []
            pocket_files = [f for f in os.listdir(out_dir) if f.endswith(".pdb") and "env" not in f]
            pockets=[]

            for file in pocket_files:
                s=Structure.from_file(name=f"{self.name}_{file}", file=os.path.join(out_dir, file))
                pockets.append(s)

            return pockets

    def to_3di(self, chain):
        "for a chain convert the structure to 3di"
        atoms = self._get_chain(chain)
        aa_atoms = atoms[filter_amino_acids(atoms)]
        seq = str(alphabet.to_3di(aa_atoms)[0][0])
        return Sequence(name=self.info.name + "_" + chain, sequence=seq, seq_type="3di")

    def sequence(self):
        "extract the aa sequence from the pdb, if there are gap there will be - if there are uknown aa there will be an X"
        seqs = []
        for chain in self.info.chains:
            chain_atoms = self._get_chain(chain)
            aa_atoms = chain_atoms[filter_amino_acids(chain_atoms)]
            if len(aa_atoms) == 0:
                continue
            seq = to_sequence(aa_atoms, allow_hetero=True)[0][0]
            seq = str(seq)
            seqs.append(Sequence(name=self.info.name + "_" + chain, sequence=seq, seq_type="protein"))
        if len(seqs) == 1:
            return seqs[0]
        else:
            return SequenceList(seqs)

    def tm_score(self, other):
        """
        run us-align to get the tm score between 2 structures
        :param other: other structure
        :return: retun the tm score
        """
        assert(isinstance(other, Structure))
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, f"{self.name}.pdb")
            f2 = os.path.join(tmpdir, f"{other.name}.pdb")

            self.write(f1)
            other.write(f2)

            cmd = ["USalign", f1, f2, "-outfmt", "0"]
            run = subprocess.run(cmd, capture_output=True, text=True)
            if run.returncode != 0:
                raise RuntimeError(run.stderr)
            for line in run.stdout.splitlines():
                if "TM-score=" in line:
                    return float(line.split("=")[1].split()[0])
            return None

    def _get_chain(self, chain_id):
        return self.info.atoms[self.info.atoms.chain_id == chain_id]

    def write(self, fpath):
        if len(self.info.atoms) > 99999:
            warnings.warn("Atom count exceeds PDB format capacity (99,999). Some atom serial numbers may be truncated.")
        file=PDBFile()
        file.set_structure(self.info.atoms)
        file.write(fpath)

    def contacts(self, chain_id1, chain_id2, cutoff=5.0, level="atom", measure="any"):
        """
        Get contacts between two chains in the structure.
        :param chain_id1: chain 1
        :param chain_id2: chain 2
        :param cutoff: distance cutoff to be called contacting default 5A
        :param level: if "atom" return the contacting atom, if residue return the resdiues
        :measure: how the contact is calculated, if any any atom within the cutoff range will be included
        if CA only alpha carbons are counted
        :return:a list of atoms, residues etc.
        """
        chain1 = self._get_chain(chain_id1)
        chain2 = self._get_chain(chain_id2)
        if measure == "CA":
            chain1 = chain1[chain1.atom_name == "CA"]
            chain2 = chain2[chain2.atom_name == "CA"]

        contacts = []
        if len(chain1) == 0 or len(chain2) == 0:
            return contacts

        dists = np.linalg.norm(chain1.coord[:, np.newaxis, :] - chain2.coord[np.newaxis, :, :], axis=-1)
        indices1, indices2 = np.where(dists < cutoff)

        for i, j in zip(indices1, indices2):
            dist = float(dists[i, j])
            if level == "atom":
                contacts.append({chain_id1: int(i), chain_id2: int(j), "distance": dist})
            elif level == "residue":
                contacts.append({chain_id1: int(chain1[i].res_id), chain_id2: int(chain2[j].res_id), "distance": dist})

        return contacts

    def __repr__(self):
        return "Structure(name={}, chains={})".format(self.info.name, ",".join(self.info.chains))

    def __str__(self):
        return self.name

    def __getitem__(self, key: Union[str, int, slice, Tuple[str, Union[int, str]]]):
        """
        Support indexing:
          - structure['A'] -> returns chain atoms (Biotite AtomArray slice)
          - structure[0] -> returns first chain atoms (by order in self.chains)
          - structure['A', 100] -> returns list of atoms belonging to residue id 100 in chain A
          - structure[0:2] -> list of chain AtomArray slices for the first two chains
        """
        if isinstance(key, str):
            return self._get_chain(key)
        if isinstance(key, int):
            chain_id = self.info.chains[key]
            return self._get_chain(chain_id)
        if isinstance(key, slice):
            sel = self.info.chains[key]
            return [self._get_chain(ch) for ch in sel]
        if isinstance(key, tuple) and len(key) == 2:
            chain_id, resid = key
            chain = self._get_chain(chain_id)
            atoms = [atom for atom in chain if atom.res_id == resid]
            return atoms
        raise KeyError(f"Unsupported key type: {type(key)}")

    @classmethod
    def from_file(cls, name, file=None, source=None, destination=None, id=None):
        if file is not None:
            if not os.path.exists(file):
                raise FileNotFoundError(f"File not found: {file}")

            structure=_read(file)

        if file is None and id is not None:
            if destination is None:
                raise ValueError("destination must be provided when downloading by id")
            file=os.path.abspath(download(id, source, destination))
            structure = _read(file)

        if file is None and id is None:
            raise ValueError("You must provide a file or an id as well as a source and destination")

        return cls(name, structure)


