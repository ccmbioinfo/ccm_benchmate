import os
import shutil

from benchmate.genome.genome import Genome as BaseGenome


class Genomes:
    """
    project integration of the genome class, this is so that instead of sqlite we are using the postgres server of the project
    """
    def __init__(self, config, project):
        """
        create a genome instance using the project database and config
        :param config: genome section of config.yaml
        :param project: project class instance
        """
        self.config=config
        self.project=project
        self.genomes={}
        if "genomes" in self.config:
            for name, info in self.config["genomes"].items():
                description=info.get("description", "")
                files=info.get("files", {})
                genome_path=os.path.join(self.config.get("genome_path", "."), name)
                os.makedirs(genome_path, exist_ok=True)
                for file_key in files.keys():
                    if files[file_key] and os.path.isfile(files[file_key]):
                        shutil.copy(files[file_key], genome_path)
                        files[file_key]=os.path.join(genome_path, os.path.basename(files[file_key]))

                g=BaseGenome(
                    genome_fasta=files.get("genome_fasta"),
                    gtf=files.get("gtf"),
                    name=name,
                    db_conn=self.project.kb.engine,
                    project=self.project,
                    description=description,
                    proteome_fasta=files.get("proteome_fasta"),
                    transcriptome_fasta=files.get("transcriptome_fasta"),
                    standalone=False,
                    create=True
                )
                self.genomes[name]=g

    def add_genome(self, name, gtf, genome_fasta, description="", transcriptome_fasta=None, proteome_fasta=None, create=True):
        """
        Dynamically add and register a new genome instance to the project.
        """
        g = BaseGenome(
            genome_fasta=genome_fasta,
            gtf=gtf,
            name=name,
            db_conn=self.project.kb.engine,
            project=self.project,
            description=description,
            proteome_fasta=proteome_fasta,
            transcriptome_fasta=transcriptome_fasta,
            standalone=False,
            create=create
        )
        self.genomes[name] = g
        return g

    def __getitem__(self, item):
        return self.genomes[item]

    def get(self, item, default=None):
        return self.genomes.get(item, default)

    def __contains__(self, item):
        return item in self.genomes

    def __iter__(self):
        return iter(self.genomes)

    def __len__(self):
        return len(self.genomes)

    def keys(self):
        return self.genomes.keys()

    def values(self):
        return self.genomes.values()

    def items(self):
        return self.genomes.items()