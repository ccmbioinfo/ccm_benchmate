import os
import io
import shutil
from pathlib import Path
from functools import partial
from hashlib import md5
from PIL import Image
import warnings
import json

from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound

from benchmate.utils.general_utils import DataIntegrityError
from benchmate.inference.inference import Inference

#sequence
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from benchmate.sequence.sequence import Sequence as BaseSequence

#molecule
from rdkit import Chem
from benchmate.molecule.molecule import Molecule as BaseMolecule
from molecule.molecule import MoleculeInfo

#structure
from benchmate.structure.utils import *
from benchmate.structure.structure import Structure as BaseStructure, StructureInfo
from biotite.structure.io.pdb import PDBFile

#variants
from benchmate.variant.variant import SequenceVariant as BaseSequenceVariant
from benchmate.variant.variant import StructuralVariant as BaseStructuralVariant
from benchmate.variant.variant import TandemRepeatVariant as BaseTandemRepeatVariant

#genomes
from benchmate.genome.genome import Genome as BaseGenome

#apis
from benchmate.apis.utils import ApiCall as BaseApiCall
from benchmate.apis.ncbi import Ncbi
from benchmate.apis.ensembl import Ensembl
from benchmate.apis.alphagenome import AlphaGenome
from benchmate.apis.biogrid import BioGrid
from benchmate.apis.intact import IntAct
from benchmate.apis.ols import OLS
from benchmate.apis.reactome import Reactome
from benchmate.apis.rnacentral import RnaCentral
from benchmate.apis.stringdb import StringDb
from benchmate.apis.uniprot import UniProt
from benchmate.apis.ebi import EBI

#alignment
from benchmate.alignment.blast import Blast
from benchmate.alignment.mmseqs import MMSeqs
from benchmate.alignment.foldseek import FoldSeek
from benchmate.alignment.folddisco import FoldDisco

#literature
from benchmate.literature.literature import LitSearch as BaseLitSearch
from benchmate.literature.literature import OpenAlex
from benchmate.literature.literature import Paper as BasePaper


# This is not initiated with the project class instance because this is the representation of a paper
# It will be called when he project tries to retrieve a paper.
class Paper(BasePaper):
    def __init__(self, paper_id):
        super().__init__(paper_id)

    def to_kb(self, project):
        papers_table = project.kb.db_tables["papers"]
        figures_table = project.kb.db_tables["figures"]
        tables_table = project.kb.db_tables["tables"]
        chunked_text_table = project.kb.db_tables["body_text_chunked"]
        references_table = project.kb.db_tables["references"]
        related_works_table = project.kb.db_tables["related_works"]
        cited_by_table = project.kb.db_tables["cited_by"]

        # check if paper exists
        check_stmt = papers_table.select(papers_table.c.id).where(papers_table.c.id == self.info.id)
        existing = project.kb.session().execute(check_stmt).scalars().fetchall()
        if len(existing) > 1:
            raise DataIntegrityError(f"Found more than one paper with id:{self.info.id}")

        if len(existing) == 1:
            warnings.warn(f"Paper with openlalex id {self.info.id} already exists within the project")
            return existing[0]

        stmt = insert(papers_table.c.project_id,
                      papers_table.c.paper_id,
                      papers_table.c.external_ids,
                      papers_table.c.title,
                      papers_table.c.abstract,
                      papers_table.c.abstract_embeddings,
                      papers_table.c.download_links,
                      papers_table.c.file_paths,
                      papers_table.c.full_json,
                      papers_table.c.authors,
                      papers_table.c.publication_date,
                      papers_table.c.venue,
                      papers_table.c.full_text).values(
            self.info.id, self.info.external_ids, self.info.title, self.info.abstract, self.info.abstract_embeddings,
            self.info.download_links, self.info.file_paths, self.info.full_json, self.info.authors,
            self.info.publication_date, self.info.venue, self.info.text).returning(papers_table.c.id)

        paper_id = project.kb.session().execute(stmt).scalars().one()

        if self.info.figures is not None:
            for i in range(len(self.info.figures)):
                img = Image.open(self.info.figures[i])
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG")
                img_bytes = img_byte_arr.getvalue()
                figure_stms = insert(figures_table.c.paper_id, figures_table.c.image_blob,
                                     figures_table.c.ai_caption,
                                     figures_table.c.figure_embeddings,
                                     figures_table.c.figure_interpretation_embeddings).values(paper_id,
                                                                                              img_bytes,
                                                                                              self.info.figure_interpretation[
                                                                                                  i],
                                                                                              json.dumps(
                                                                                                  self.info.figure_embeddings[
                                                                                                      i].tolist()),
                                                                                              self.info.figure_interpretation_embeddings[
                                                                                                  i]
                                                                                              )
                project.kb.session().execute(figure_stms)

        if self.info.tables is not None:
            for i in range(len(self.info.tables)):
                img = Image.open(self.info.tables[i])
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG")
                img_bytes = img_byte_arr.getvalue()
                table_smts = insert(tables_table.c.paper_id, tables_table.c.image_blob,
                                    tables_table.c.ai_caption,
                                    tables_table.c.table_embeddings,
                                    tables_table.c.table_interpretation_embeddings).values(paper_id,
                                                                                           img_bytes,
                                                                                           self.info.table_interpretation[
                                                                                               i],
                                                                                           json.dumps(
                                                                                               self.info.table_embeddings[
                                                                                                   i].tolist()),
                                                                                           self.info.table_interpretation_embeddings[
                                                                                               i]
                                                                                           )
                project.kb.session().execute(table_smts)

        # we will check if you have embedded them
        if self.info.text_chunks is not None:
            for i in range(len(self.info.text_chunks)):
                chunk_stms = insert(chunked_text_table.c.paper_id,
                                    chunked_text_table.c.chunk_id,
                                    chunked_text_table.c.chunk,
                                    chunked_text_table.c.chunk_embeddings).values(paper_id,
                                                                                  self.info.text_chunks[i][0],
                                                                                  self.info.text_chunks[i][1],
                                                                                  self.info.chunk_embeddings[i].tolist())
                project.kb.session().execute(chunk_stms)

        if self.info.references is not None:
            for paper in self.info.references:
                existing = select(papers_table.c.paper_id).where(papers_table.c.paper_id == paper.id)
                ref_id = project.kb.session().execute(existing).scalar()
                if ref_id is None:
                    ref_id = paper.to_kb(project)
                stms = insert(references_table.c.paper_id, references_table.c.id, ).values(paper_id, ref_id)
                project.kb.session().execute(stms)

        if self.info.related_works is not None:
            for paper in self.info.related_works:  #
                existing = select(papers_table.c.paper_id).where(papers_table.c.source_id == paper.id)
                related_id = project.kb.session().execute(existing).scalar()
                if related_id is None:
                    related_id = paper.to_kb(project)
                stms = insert(related_works_table.c.paper_id, related_works_table.c.id, ).values(paper_id, related_id)
                project.kb.session().execute(stms)

        if self.info.cited_by is not None:
            for paper in self.info.cited_by:
                existing = select(papers_table.c.paper_id).where(papers_table.c.source_id == paper.id,
                                                                 papers_table.c.id_type == paper.id_type)
                cited_id = project.kb.session().execute(existing).scalar()
                if cited_id is None:
                    cited_id = paper.to_kb(project)
                stms = insert(cited_by_table.c.paper_id, cited_by_table.c.id, ).values(paper_id, cited_id)
                project.kb.session().execute(stms)

        project.kb.session().commit()
        return paper_id

    @classmethod
    def from_kb(cls, project, id):
        papers_table = project.kb.db_tables["papers"]
        figures_table = project.kb.db_tables["figures"]
        tables_table = project.kb.db_tables["tables"]
        chunked_text_table = project.kb.db_tables["body_text_chunked"]
        references_table = project.kb.db_tables["references"]
        related_works_table = project.kb.db_tables["related_works"]
        cited_by_table = project.kb.db_tables["cited_by"]

        # this is the part that needs fixing
        selection = select(papers_table.c.id,
                           papers_table.c.external_ids,
                           papers_table.c.title,
                           papers_table.c.abstract,
                           papers_table.c.abstract_embeddings,
                           papers_table.c.download_links,
                           papers_table.c.file_paths,
                           papers_table.c.full_json,
                           papers_table.c.authors,
                           papers_table.c.publication_date,
                           papers_table.c.venue,
                           papers_table.c.full_text).where(papers_table.c.paper_id == id)

        paper_info = project.kb.session().execute(selection).fetchall()

        if len(paper_info) > 1:
            raise DataIntegrityError("There are multiple papers with the id {}".format(id))
        elif len(paper_info) == 0:
            raise NoResultFound("Could not find a paper with id:{}".format(id))
        else:

            paper = cls(paper_id=paper_info[0][0])
            paper.external_ids = paper_info[0][1]
            paper.title = paper_info[0][2]
            paper.abstract = paper_info[0][3]
            paper.abstract_embeddings = paper_info[0][4]
            paper.download_links = paper_info[0][5]
            paper.file_paths = paper_info[0][6]
            paper.full_json = paper_info[0][7]
            paper.authors = paper_info[0][8]
            paper.publication_date = paper_info[0][9]
            paper.venue = paper_info[0][10]
            paper.text = paper_info[0][11]

        figures = select(figures_table.c.image_blob,
                         figures_table.c.figure_embeddings,
                         figures_table.c.ai_caption,
                         figures_table.c.figure_interpretation_embeddings).where(figures_table.c.paper_id == id)
        figures = project.kb.session().execute(figures).fetchall()

        if len(figures) == 0:
            paper.figures = None
        else:
            paper.figures = [Image.open(io.BytesIO(figure[0])) for figure in figures]
            paper.figure_embeddings = [figure[1] for figure in figures]
            paper.figure_interpretation = [figure[2] for figure in figures]
            paper.figure_interpretation_embeddings = [figure[3] for figure in figures]

        tables = select(tables_table.c.image_blob,
                        tables_table.c.table_embeddings,
                        tables_table.c.ai_caption,
                        tables_table.c.table_interpretation_embeddings).where(tables_table.c.paper_id == id)
        tables = project.kb.session().execute(tables).fetchall()
        if len(tables) == 0:
            paper.tables = None
        else:
            paper.tables = [Image.open(io.BytesIO(table[0])) for table in tables]
            paper.table_embeddings = [table[1] for table in tables]
            paper.table_interpretation = [table[2] for table in tables]
            paper.table_interpretation_embeddings = [table[3] for table in tables]

        chunks = select(chunked_text_table.c.chunk,
                        chunked_text_table.c.chunk_embeddings).where(chunked_text_table.c.paper_id == id)
        chunks = project.kb.session().execute(chunks).fetchall()
        if len(chunks) == 0:
            paper.text_chunks = None
        else:
            paper.text_chunks = [chunk[0] for chunk in chunks]
            paper.chunk_embeddings = [chunk[1] for chunk in chunks]

        references = select(references_table.c.target_id).where(references_table.c.paper_id == id)
        references = project.kb.session().execute(references).fetchall()
        if len(references) == 0:
            paper.references = None
        else:
            refs = []
            for ref in references:
                ref_paper = cls.from_kb(project, ref[1])
                refs.append(ref_paper)
            paper.references = refs

        cited_by = select(cited_by_table.c.target_id).where(cited_by_table.c.paper_id == id)
        cited_by = project.kb.session().execute(cited_by).fetchall()
        if len(cited_by) == 0:
            paper.cited_by = None
        else:
            refs = []
            for ref in cited_by:
                ref_paper = cls.from_kb(project, ref[1])
                refs.append(ref_paper)
            paper.cited_by = refs

        related_works = select(related_works_table.c.target_id).where(related_works_table.c.paper_id == id)
        related_works = project.kb.session().execute(related_works).fetchall()
        if len(related_works) == 0:
            paper.related_works = None
        else:
            refs = []
            for ref in related_works:
                ref_paper = cls.from_kb(project, ref[1])
                refs.append(ref_paper)
            paper.related_works = refs

        return paper

class LitSearch(BaseLitSearch):
    def __init__(self, config):
        self.config=config
        super().__init__()
        self.openalex=OpenAlex(self["config"]["openalex_api_key"])
        os.makedirs(self.config["pdf_path"], exist_ok=True)
        self.search=partial(self.search,openalex=self.openalex)

class ApiCall(BaseApiCall):
    def to_kb(self, project):
        api_table = project.kb.db_tables["api_call"]
        params = {"args": self.args, "kwargs": self.kwargs}
        # add main results

        stmt = insert(api_table).values(
            project_id=project.project_id,
            class_name=self.class_name,
            method_name=self.method_name,
            params=params,
            query_time=self.query_time,
            results=self.results,
        ).returning(api_table.c.id)

        result = project.kb.session().execute(stmt)
        new_id = result.scalar_one()
        project.kb.session().commit()
        # add chunks
        return new_id

    @classmethod
    def from_kb(cls, project, id):
        api_table = project.kb.db_tables["api_call"]

        main_stmt = select(api_table.c.class_name,
                           api_table.c.method_name,
                           api_table.c.init_kwargs,
                           api_table.c.params,
                           api_table.c.results,
                           api_table.c.query_time,
                           api_table.c.flat_results).where(api_table.c.id == id)

        results = project.kb.session().execute(main_stmt).fetchall()
        if len(results) == 0:
            raise NoResultFound("Could not find an api call with id {}".format(id))

        if len(results) > 1:
            raise DataIntegrityError("Found more than one api call with id {}".format(id))

        params = results[0][3]
        args = params.get("args")
        kwargs = params.get("kwargs")

        call = cls(
            class_name=results[0][0],
            method_name=results[0][1],
            init_kwargs=results[0][2],
            args=args,
            kwargs=kwargs,
            query_time=results[0][4]
        )
        return call

class Apis:
    def __init__(self, config, project):
        self.config=config
        self.email=self.config["email"]
        self.biogrid_api_key=self.config["biogrid_api_key"]
        self.alphagenome_api_key=self.config["alphagenome_api_key"]

        self.call_class=ApiCall(project)

        #setup the classes
        self.alphagenome=AlphaGenome(self.alphagenome_api_key)

        self.biogrid=BioGrid(self.biogrid_api_key)
        self.biogrid.call_class=self.call_class

        self.ebi=EBI()

        self.ensembl=Ensembl()
        self.ensembl.call_class=self.call_class

        self.intact=IntAct()
        self.intact.call_class=self.call_class

        self.ncbi=Ncbi(email=self.email)
        self.ncbi.call_class=self.call_class

        self.ols=OLS()
        self.ols.call_class=self.call_class

        self.reactome=Reactome()
        self.reactome.call_class=self.call_class

        self.rnacentral=RnaCentral()
        self.rnacentral.call_class=self.call_class

        self.stringdb=StringDb()
        self.stringdb.call_class=self.call_class

        self.uniprot=UniProt()
        self.uniprot.call_class=self.call_class

class Genomes(BaseGenome):
    def __init__(self, config, project):
        self.config=config
        self.project=project
        self.genomes={}
        for name, info in self.config["genomes"].items():
            #info:
            description=self.config["genomes"]["name"]["description"]
            files=self.config["genomes"][name]["files"]
            for file in files.keys():
                if file is not None:
                    genome_path=os.path.join(config["genome_path"], name)
                    os.makedirs(genome_path, exist_ok=False)
                    shutil.copy(files[file], genome_path)
                    files[file]=os.path.join(genome_path, os.path.basename(files[file]))
                else:
                    continue

            g=super().__init__(genome_fasta=files["genome_fasta"],
                              gtf=files["gtf"],
                              name=name,
                              db_conn=self.project.kb.engine,
                              description=description,
                              proteome_fasta=files["proteome_fasta"],
                              transcriptome_fasta=files["transcriptome_fasta"],
                              standalone=False,
                              create=True
            )
            self.genomes[name]=g

class Alignment:
    def __init__(self, config):
        self.config=config
        self.blast=Blast()
        self.blast.find_local_databases(config["blast_db_root"])
        self.blast.create_db=partial(self.blast.create_db, output_path=self.config["blast_db_root"])
        self.mmseqs=MMSeqs()
        self.mmseqs.find_local_databases(config["mmseq_db_root"])
        self.mmseqs.download_database=partial(self.mmseqs.download_database, location=self.config["mmseqs_db_root"])
        self.foldseek=FoldSeek()
        self.foldseek.find_local_databases(config["foldseek_db_root"])
        self.foldseek.download_database=partial(self.foldseek.download_database, location=self.config["foldseek_db_root"])
        self.folddisco = FoldDisco()
        self.folddisco.find_local_databases(config["folddisco_db_root"])
        self.folddisco.create_index = partial(self.folddisco.create_index, db_path=self.config["folddisco_db_root"])

class SequenceVariant(BaseSequenceVariant):
    def to_kb(self, project):
        table = project.kb.db_tables["sequencevariant"]
        stmt = insert(table).values(id=self.id, chrom=self.chrom, pos=self.pos,
                                    ref=self.ref, alt=self.alt, length=self.length,
                                    annotations=self.annotations)
        project.kb.session.execute(stmt)
        project.kb.session.commit()

    @classmethod
    def from_kb(cls, project, id):
        table = project.kb.db_tables["sequencevariant"]
        stmt = select(table).where(table.c.id == id).fetchall()
        results = project.kb.session.execute(stmt)
        if len(results) == 0:
            raise NoResultFound(f"SequenceVariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple sequenceVariant with id {id} found")

        results = results[0]
        variant = cls(
            id=results.id,
            chrom=results.chrom,
            pos=results.pos,
            ref=results.ref,
            alt=results.alt,
            length=results.length,
            annotations=results.annotations,
        )
        return variant

class StructuralVariant(BaseStructuralVariant):
    def to_kb(self, project):
        table = project.kb.db_tables["structuralvariant"]
        stmt = insert(table).values(id=self.id, chrom=self.chrom, pos=self.pos,
                                    svlen=self.svlen, cn=self.cn, cistart=self.cistart,
                                    ciend=self.ciend, annotations=self.annotations)
        project.kb.session.execute(stmt)
        project.kb.session.commit()

    @classmethod
    def from_kb(cls, project):
        table = project.kb.db_tables["structuralvariant"]
        stmt = select(table).where(table.c.id == id).fetchall()
        results = project.kb.session.execute(stmt)
        if len(results) == 0:
            raise NoResultFound(f"structuralvariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple structuralvariant with id {id} found")

        results = results[0]
        variant = cls(
            id=results.id,
            chrom=results.chrom,
            pos=results.pos,
            svlen=results.svlen,
            cn=results.cn,
            cistart=results.cistart,
            ciend=results.cient,
            annotations=results.annotations,
        )
        return variant

class TandemRepeatVariant(BaseTandemRepeatVariant):
    def to_kb(self, project):
        table = project.kb.db_tables["tandemrepeatvariant"]
        stmt = insert(table).values(id=self.id, chrom=self.chrom, pos=self.pos,
                                    al=self.al, annotations=self.annotations)
        project.kb.session.execute(stmt)
        project.kb.session.commit()

    @classmethod
    def from_kb(cls, project):
        table = project.kb.db_tables["tandemrepeatvariant"]
        stmt = select(table).where(table.c.id == id).fetchall()
        results = project.kb.session.execute(stmt)
        if len(results) == 0:
            raise NoResultFound(f"tandemrepeatvariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple tandemrepeatvariant with id {id} found")

        results = results[0]
        variant = cls(
            id=results.id,
            chrom=results.chrom,
            pos=results.pos,
            ref=results.ref,
            alt=results.alt,
            annotations=results.annotations,
            motif=results.motif,
            al=results.al
        )
        return variant

class Structure(BaseStructure):
    def __init__(self, config, name, atoms, annotations):
        self.config = config
        self._pdbs()
        super().__init__(name, atoms, annotations)


    def _pdbs(self):
        os.makedirs(self.config["pdb_path]"], exist_ok=True)

    def to_kb(self, project):
        structure_table = project.kb.db_tables["structure"]

        # 1. Convert AtomArray -> PDB text
        pdb_file = PDBFile()
        pdb_file.set_structure(self.info.atoms)
        buf = io.StringIO()
        pdb_file.write(buf)
        pdb_text = buf.getvalue()

        # after you build pdb_text as a str, convert to bytes
        pdb_bytes = pdb_text.encode("utf-8")

        # 2. Build row data (atoms as TEXT) in a dictionary
        row_data = {
            "project_id": project.id,
            "name": self.name,
            "chains": self.info.chains,
            "atoms": pdb_bytes,  # plain text, no gzip
            "annotations": self.info.annotations,
            "hash":md5(pdb_bytes).hexdigest(),
        }
        # insert into structure table
        stmt = structure_table.insert().values(**row_data).returning(structure_table.c.id)
        result = project.session.execute(stmt)[0]
        project.session.commit()

        return result

    @classmethod
    def from_kb(cls, project, id):
        structure_table = project.kb.db_tables["structure"]
        stmt = select(structure_table).where(structure_table.c.id == id)

        results = project.kb.session.execute(stmt).fetchall()

        if len(results) == 0:
            raise NoResultFound(f"Could not find a molecule with id {id}")
        if len(results) > 1:
            raise DataIntegrityError(f"Found more than one molecule with id {id}")

        # the first row
        row = results[0]._mapping

        name = row["name"]
        chains = row["chains"]

        # pdb pay load from the to_kb
        atoms_blob = row["atoms"]
        annotations = row["annotations"]

        # ran into attribute errors, memoryview to bytes , if bytes decode to utf- 8, crash if anything else
        if isinstance(atoms_blob, memoryview):
            atoms_blob = atoms_blob.tobytes()
        elif isinstance(atoms_blob, str):
            atoms_text = atoms_blob
        elif isinstance(atoms_blob, bytes):
            atoms_text = atoms_blob.decode("utf-8")
        else:
            raise TypeError(f"Unexpected atoms type: {type(atoms_blob)}")

        if not isinstance(atoms_blob, str):
            atoms_text = atoms_blob.decode("utf-8")

        # rebuild biotite struct
        buf = io.StringIO(atoms_text)
        pdb_file = PDBFile.read(buf)
        atom_array = pdb_file.get_structure(model=1)
        return cls(name, atom_array, annotations)

    @classmethod
    def from_file(cls, config, name, file, source, destination, id):
        if file is not None:
            if not os.path.exists(file):
                raise FileNotFoundError(f"File not found: {file}")

            structure=super().from_file(file)

        if file is None and id is not None:
            file=os.path.abspath(download(id, source, destination))
            structure = super().from_file(file)

        if file is None and id is None:
            raise ValueError("You must provide a file or an id as well as a source and destination")

        return cls(config, name, structure)

class Molecule(BaseMolecule):
    def __init__(self, config, name, smiles):
        self.fingerprint_dim=config["fingerprint_dim"]
        self.fingerprint_radius=config["fingerprint_radius"]
        super().__init__(name, smiles, self.fingerprint_dim, self.fingerprint_radius)

    @classmethod
    def from_kb(cls, project, id):
        molecule_table = project.kb.db_tables["molecule"]

        stmt = (
            select(
                molecule_table.c.name,
                molecule_table.c.smiles,
                molecule_table.c.fingerprint_dim,
                molecule_table.c.fingerprint_radius,
                molecule_table.c.ecfp4,
                molecule_table.c.fcfp4,
                molecule_table.c.maccs,
                molecule_table.c.inchikey,
                molecule_table.c.properties,
                molecule_table.c.annotations,
            )
            .where(molecule_table.c.id == id)
        )

        results = project.kb.session().execute(stmt).fetchall()

        if len(results) == 0:
            raise NoResultFound(f"Could not find a molecule with id {id}")

        if len(results) > 1:
            raise DataIntegrityError(f"Found more than one molecule with id {id}")

        row = results[0]

        info = MoleculeInfo(
            name=row[0],
            smiles=row[1],
            fingerprint_dim=row[2],
            fingerprint_radius=row[3],
            ecfp4=row[4],
            fcfp4=row[5],
            maccs=row[6],
            inchi=row[7],
            properties=row[8],
            features=row[9],
        )

        # restore RDKit mol
        info.mol = Chem.MolFromSmiles(info.smiles)
        molecule = cls(name=info.name, smiles=info.smiles)
        molecule.info = info
        return molecule

    def to_kb(self, project):
        molecule_table = project.kb.db_tables["molecule"]

        stmt = (molecule_table.insert().values(
                project_id=project.project_id,
                name=self.info.name,
                smiles=self.info.smiles,
                fingerprint_dim=self.info.fingerprint_dim,
                fingerprint_radius=self.info.fingerprint_radius,
                ecfp4=self.info.ecfp4,
                fcfp4=self.info.fcfp4,
                maccs=self.info.maccs,
                inchikey=self.info.inchikey,
                properties=self.info.properties,
                annotations=self.info.features,
            )
            .returning(molecule_table.c.id)
        )

        result = project.kb.session().execute(stmt)
        mol_id = result.scalar_one()
        project.kb.session().commit()

        return mol_id

class Sequence(BaseSequence):
    def __init__(self, config, name, sequence, seq_type, features):
        self.config=config
        self._fastas()
        super().__init__(name, sequence, seq_type, features)

    @classmethod
    def from_fasta(cls, config, file):
        seq=super().from_fasta(file)
        cls(config, seq.name, seq.sequence, seq.seq_type, seq.features)
        return cls

    @classmethod
    def from_kb(cls, project, id):
        sequence_table = project.kb.db_tables["sequence"]
        stmt = select(sequence_table).where(sequence_table.c.id == id)
        result = project.kb.session.execute(stmt)
        info = result.scalar_one()
        return cls(name=info.name, sequence=info.sequence, seq_type=info.seq_type, features=info.features)

    def to_kb(self, project):
        sequence_table = project.kb.db_tables["sequence"]
        stmt = sequence_table.insert().values(project_id=project.project_id,
                                              name=self.info.name,
                                              sequence=self.info.sequence,
                                              seq_type=self.info.seq_type,
                                              annotations=self.info.annotations,
                                              hash=md5(self.info.sequence).hexdigest()).returning(sequence_table.c.id)
        result = project.kb.session.execute(stmt)
        seq_id = result.scalar.one()
        project.kb.session.commit()

        if self.seq_type=="dna":
            fasta=os.path.join(self.config["fasta_root"], "dna.fa")
        elif self.seq_type=="rna":
            fasta=os.path.join(self.config["fasta_root"], "rna.fa")
        elif self.seq_type=="protein":
            fasta=os.path.join(self.config["fasta_root"], "protein.fa")
        elif self.seq_type=="3di":
            fasta=os.path.join(self.config["fasta_root"], "tdi.fa")

        new_record=SeqRecord(Seq(self.info.sequence), id=result, description=self.info.name)

        with open(fasta, "a") as f:
            SeqIO.write(new_record, f, "fasta")

        return seq_id

    def _fastas(self):
        os.makedirs(self.config["fasta_root"], exist_ok=True)
        files = ["dna.fa", "rna.fa", "protein.fa", "tdi.fa"]  # tdi is 3di
        for file in files:
            if os.path.exists(os.path.join(self.config["fasta_root"], file)):
                continue
            else:
                Path(os.path.join(self.config["fasta_root"], file)).touch()
