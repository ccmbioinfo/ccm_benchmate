import os
import shutil

from benchmate.genome.genome import Genome as BaseGenome


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