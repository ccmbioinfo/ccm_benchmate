import pandas as pd
import torch

from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein, LogitsConfig

from Bio.Blast import NCBIWWW
from Bio.Blast import NCBIXML
from io import StringIO # Use StringIO to handle the XML string directly

#TODO this is a generic embeddings function that will call others
def embeddings(sequence, model, normalize=False):
    pass

#TODO
def hf_embeddings(model, normalize=False):
    pass


def esm3_embeddings(sequence, model, normalize=False, device="cuda"):
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if model not in ["esmc_300m", "esmc_600m"]:
        raise ValueError("Invalid model name")
    protein = ESMProtein(sequence)
    client = ESMC.from_pretrained(model).to(device)  # or "cpu"
    protein_tensor = client.encode(protein)
    logits_output = client.logits(
        protein_tensor, LogitsConfig(sequence=True, return_embeddings=True)
    )
    embeddings = logits_output.embeddings
    if normalize:
        embeddings = logits_output.embeddings[0].mean(dim=0)
    return embeddings


def blast_search(program, database, sequence, expect_threshold=10.0, hitlist_size=50):
    if not all([program, database, sequence]):
        raise ValueError("Program, database, and sequence are required parameters.")

    try:
        result_handle = NCBIWWW.qblast(
            program=program,
            database=database,
            sequence=sequence,
            expect=expect_threshold,
            hitlist_size=hitlist_size
        )

        blast_result_xml = result_handle.read()
        result_handle.close()

        if not blast_result_xml or "Status=WAITING" in blast_result_xml or "Status=FAILED" in blast_result_xml:
             if "Message" in blast_result_xml:
                 try:
                     message_start = blast_result_xml.find("<Message") + len("<Message")
                     message_start = blast_result_xml.find(">", message_start) + 1
                     message_end = blast_result_xml.find("</Message>")
                     if message_start > 0 and message_end > message_start:
                         error_message = blast_result_xml[message_start:message_end]
                         print(f"Error message from NCBI: {error_message}")
                 except Exception as e:
                     print(f"Could not parse specific error message: {e}")
             return None # Indicate failure or no results

        xml_handle = StringIO(blast_result_xml)
        blast_record = NCBIXML.read(xml_handle)

        print("BLAST search completed successfully.")
        return blast_record

    except Exception as e:
        print(f"An error occurred during the BLAST search: {e}")
        raise e


def parse_blast_search(blast_record):
    alignments=[]
    if blast_record.alignments:
        for alignment in blast_record.alignments:
            results={"alignment":alignment.title,
                     "length":alignment.length,
                     "score":alignment.hsps[0].score,
                     "evalue":alignment.hsps[0].expect,
                     "query_start":alignment.hsps[0].query_start,
                     "query_end":alignment.hsps[0].query_end,
                     "subject_start":alignment.hsps[0].sbjct_start,
                     "subject_end":alignment.hsps[0].sbjct_end,
                     "hit_sequence":alignment.hsps[0].sbjct,}
            alignments.append(results)
        alignments=pd.DataFrame(alignments)
    else:
        raise ValueError("No blast alignments found.")
    return alignments


