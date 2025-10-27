import os
import subprocess
from dataclasses import dataclass

from typing import List, Union, Tuple

from biotite.structure import distance, get_chains, alphabet, to_sequence
from biotite.structure.io.pdb import PDBFile
from biotite.structure.io.pdbx import CIFFile

from benchmate.structure.utils import *
from benchmate.sequence.sequence import Sequence, SequenceList

@dataclass
class StructureInfo:
    name: str
    file: str
    chains: List[str] = None


class Structure:
    def __init__(self, name, file, id=None, source="PDB", destination="."):
        """
        :param name:
        :param pdb:
        :param id:
        :param source:
        :param destination:
        """
        self.file = os.path.abspath(file)
        if file is not None:
            self.structure=self._read(file)

        if file is None and id is not None:
            file=os.path.abspath(download(id, source, destination))
            self.structure = self._read(file)

        self.info = StructureInfo(name=name, file=file)
        self.info.chains = get_chains(self.structure)

    def _read(self, file):
        if file.endswith(".pdb"):
            structure = PDBFile.read(file).get_structure()[0]
        elif file.endswith(".cif") or file.endswith(".mmcif"):
            structure = CIFFile.read(file).get_structure()[0]
        else:
            raise NotImplementedError("We can only read PDB or CIF files")
        return structure

    def align(self, other, destination):
        if self.pdb is None or other.pdb is None:
            raise ValueError("Cannot align structures without a PDB")

        command = ["mustang", "-i", os.path.abspath(self.pdb), os.path.abspath(other.pdb), "-o",
                   os.path.abspath(destination), "-r", "ON"]
        process = subprocess.run(command)
        if process.returncode != 0:
            raise ValueError("There was an error aligning structures. See error below \n {}".format(process.stderr))

        aligned_pdb = os.path.abspath(destination + "results.pdb")
        rotation_file = os.path.abspath(destination + "results.rms_rot")
        html_report = os.path.abspath(destination + "results.html")
        return aligned_pdb, rotation_file, html_report

    def find_pockets(self, **kwargs):
        """
        Run fpocket on this structure and return detected pocket info.
        Returns (pocket_files, pocket_coords)
        """
        cmd_params = " ".join([f"--{k} {v}" for k, v in kwargs.items()])
        command = f"fpocket -f {self.pdb} -x -d {cmd_params}"
        run = subprocess.run(command, shell=True, capture_output=True, text=True)

        if run.returncode != 0:
            raise RuntimeError(run.stderr)

        results_dir = self.pdb.replace(".pdb", "_out")
        pocket_files = [f for f in os.listdir(results_dir) if f.endswith(".pdb")]
        pocket_coords = [get_pocket_dimensions(os.path.join(results_dir, f)) for f in pocket_files]

        return pocket_files, pocket_coords

    def to_3di(self, chain):
        chain=self._get_chain(chain)
        seq, _ = str(alphabet.to_3di(chain)[0])
        return Sequence(name=self.info.name + "_" + chain.chain_id, sequence=seq, seq_type="3di")

    def sequence(self):
        seqs=[]
        for chain in self.info.chains:
            chain_atoms = self._get_chain(chain)
            seq=to_sequence(chain_atoms, allow_hetero=True)[0][0]
            seq = str(seq)
            seqs.append(Sequence(name=self.info.name + "_" + chain, sequence=seq, seq_type="protein"))
        if len(seqs) == 1:
            return seqs[0]
        else:
            return SequenceList(seqs)

    def tm_score(self, other):
        assert(isinstance(other, Structure))
        cmd = ["USalign", self.pdb, other.pdb, "-outfmt", "2"]
        run = subprocess.run(cmd, capture_output=True, text=True)
        if run.returncode != 0:
            raise RuntimeError(run.stderr)
        for line in run.stdout.splitlines():
            if "TM-score=" in line:
                return float(line.split("=")[1].split()[0])
        return None

    def _get_chain(self, chain_id):
        return self.structure[self.structure.chain_id == chain_id]

    def write(self, fpath):
        PDBFile.write(self.pdb, fpath)

    def contacts(self, chain_id1, chain_id2, cutoff=5.0, level="atom", measure="any"):
        """
        Get contacts between two chains in the structure.
        :param chain_id1:
        :param chain_id2:
        :param cutoff:
        :return:
        """
        chain1 = self._get_chain(chain_id1)
        chain2 = self._get_chain(chain_id2)
        contacts=[]
        for i in range(len(chain1)):
            for j in range(len(chain2)):
                if measure == "any":
                    dist = distance(chain1[i], chain2[j])
                elif measure=="CA":
                    if "CA" in chain1[i].atom_name and "CA" in chain2[j].atom_name:
                        dist = distance(chain1[i], chain2[j])
                    else:
                        continue
                if dist < cutoff:
                    if level == "atom":
                        contacts.append({chain_id1: i, chain_id2: j,
                                     "distance": dist})
                    elif level == "residue":
                        contacts.append({chain_id1: chain1[i].res_id, chain_id2: chain2[j].res_id,
                                     "distance": dist})

        return contacts

    def __repr__(self):
        return "Structure(name={}, pdb={}, chains={})".format(self.info.name, self.info.pdb, ",".join(self.chains))

    def __str__(self):
        return self.pdb

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
            chain_id = self.chains[key]
            return self._get_chain(chain_id)
        if isinstance(key, slice):
            sel = self.chains[key]
            return [self._get_chain(ch) for ch in sel]
        if isinstance(key, tuple) and len(key) == 2:
            chain_id, resid = key
            chain = self._get_chain(chain_id)
            atoms = [atom for atom in chain if atom.res_id == resid]
            return atoms
        raise KeyError(f"Unsupported key type: {type(key)}")

