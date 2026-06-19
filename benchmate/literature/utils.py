import os
import tarfile
import requests

from kneed import KneeLocator

class NoElbowFound(Exception):
    pass


class PaperRelevance:
    def __init__(self, description, inclusion_criteria, inference,
                 top_k_semantic=None, top_k_rerank=None):
        self.description = description
        self.inclusion_criteria = inclusion_criteria
        self.inference = inference
        self.top_k_semantic = top_k_semantic
        self.top_k_rerank = top_k_rerank

    def _format_abstracts(self, abstracts, semantic=True):
        if semantic:  # for embedding generation
            abstracts = [{"text": a} for a in abstracts]
        else:
            abstracts = [{"type": "text", "text": a} for a in abstracts]
        return abstracts

    def _get_elbow_threshold(self, scores, **kneedle_kwargs):
        """
        Given an unordered list of scores, find the elbow using kneedle and
        return the score value at that point (minimum score to keep).
        :param scores: unordered list of floats
        :param kneedle_kwargs: passed through to KneeLocator, e.g. S=1.0, interp_method="polynomial"
        :return: score value at the elbow
        """
        sorted_scores = sorted(scores, reverse=True)
        x = list(range(len(sorted_scores)))
        kl = KneeLocator(
            x, sorted_scores,
            curve="concave",
            direction="decreasing",
            **kneedle_kwargs,
        )
        if kl.elbow is None:
            raise NoElbowFound("Could not find elbow in this list of scores")
        return sorted_scores[kl.elbow]

    def _get_top_k_threshold(self, scores, top_k):
        """
        Return the score value at the top_k-th position (minimum score to keep).
        If top_k >= len(scores), returns the minimum score (keep everything).
        """
        sorted_scores = sorted(scores, reverse=True)
        if top_k >= len(sorted_scores):
            return sorted_scores[-1]
        return sorted_scores[top_k - 1]

    def _semantic(self, abstracts):
        """
        :param abstracts: list of abstract strings
        :param use_elbow: if True, use kneedle to find cutoff; if False, use top_k_semantic
        :return: (scores, threshold) — scores in the same order as input abstracts
        """
        formatted_abstracts = self._format_abstracts(abstracts, semantic=True)
        scores = self.inference.text_score(self.inclusion_criteria, formatted_abstracts)
        return scores


    def _rerank(self, abstracts):
        """
        :param abstracts: list of abstract strings
        :param use_elbow: if True, use kneedle to find cutoff; if False, use top_k_rerank
        :return: (scores, threshold) — scores in the same order as input abstracts
        """
        formatted_abstracts = self._format_abstracts(abstracts, semantic=False)
        scores = self.inference.rerank(self.description, formatted_abstracts)
        return scores

    def _split_into_n(self, lst, n):
        # k is the base size; m is the remainder distributed to the first m chunks
        k, m = divmod(len(lst), n)
        return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]



    def __call__(self, abstracts, split_n=1, use_elbow=True, **kneedle_kwargs):
        """
        Score all abstracts through semantic + rerank stages.
        :param abstracts: list of abstract strings, arbitrary order
        :param use_elbow: if True, use kneedle for both stage cutoffs; if False, use top_k_semantic/top_k_rerank
        :param kneedle_kwargs: passed through to KneeLocator if use_elbow=True
        :return: (combined_scores, combined_threshold)
            combined_scores: list aligned to input abstracts order, 0.0 for non-survivors of stage 1
            combined_threshold: minimum combined score to be considered relevant
        """
        n = len(abstracts)

        if split_n > 1:
            abstracts = self._split_into_n(abstracts, split_n)

            semantic_scores=[]
            for item in abstracts:
                s=self._semantic(item)
                semantic_scores.extend(s)
        else:
            semantic_scores=self._semantic(abstracts)

        if use_elbow:
            semantic_threshold = self._get_elbow_threshold(semantic_scores, **kneedle_kwargs)
        else:
            semantic_threshold = self._get_top_k_threshold(semantic_scores, self.top_k_rerank)

        survivor_indices = [i for i, s in enumerate(semantic_scores) if s >= semantic_threshold]
        survivor_abstracts = [abstracts[i] for i in survivor_indices]

        # Stage 2: rerank, only on survivors
        if split_n > 1:
            survivor_abstracts = self._split_into_n(survivor_abstracts, split_n)
            rerank_scores=[]
            for item in survivor_abstracts:
                s=self._rerank(item)
                rerank_scores.extend(s)
        else:
            rerank_scores=self._rerank(survivor_abstracts)

        # build positional combined scores aligned to original abstracts order
        combined_scores = [0.0] * n
        for idx, orig_i in enumerate(survivor_indices):
            combined_scores[orig_i] = rerank_scores[idx]

        # threshold computed only over survivors, never over the artificial 0.0 floor
        nonzero_scores = [c for c in combined_scores if c > 0.0]
        if use_elbow:
            combined_threshold = self._get_elbow_threshold(nonzero_scores, **kneedle_kwargs)
        else:
            combined_threshold = self._get_top_k_threshold(nonzero_scores, self.top_k_rerank)

        return combined_scores, combined_threshold


def reconstruct_abstract(inverted_index):
    """
    reconstruct the abstract of the paper because openalex only returns an inverted index
    :param inverted_index:
    :return:
    """
    if inverted_index is None:
        return None
    else:
        pos_to_token = {}
        for token, positions in inverted_index.items():
            for p in positions:
                pos_to_token[p] = token
        return " ".join(
            pos_to_token[p] for p in sorted(pos_to_token)
        )

def extract_pdfs_from_tar(file, destination, base_name):
    """
    extract all pdf files from a tar.gz file to a destination folder and return the paths to the extracted pdf files
    this is there to process pmc tar.gz files
    :param file: downloaded tar.gz file
    :param destination: where to extract the pdf files
    :return: a list of paths to the extracted pdf files
    """

    if not os.path.exists(destination):
        raise FileNotFoundError("{} does not exist.".format(destination))
    try:
        if file.endswith(".tar.gz"):
            read_str="r:gz"
        elif file.endswith(".tar.bz2"):
            read_str="r:bz2"
        elif file.endswith(".zip"):
            read_str="r:zip"
        else:
            read_str="r"

        paths=[]
        with tarfile.open(file, read_str) as tar:
            pdf_members = [
                m for m in tar.getmembers()
                if m.isfile() and m.name.lower().endswith(".pdf")
            ]
            if not pdf_members:
                return []
            for i, member in enumerate(pdf_members, start=1):
                # Naming logic
                if len(pdf_members) == 1:
                    filename = f"{base_name}.pdf"
                else:
                    filename = f"{base_name}_{i}.pdf"

                out_path = os.path.join(destination, filename)
                f = tar.extractfile(member)
                if f is None:
                    continue
                with open(out_path, "wb") as out_f:
                    out_f.write(f.read())
                paths.append(out_path)
        return paths


    except FileNotFoundError:
        print(f"Error: File not found: {file}")
        return None

    except tarfile.ReadError:
        print(f"Error: Could not open or read {file}. It might be corrupted or not a valid tar.gz file.")
        return None


def download_tar(download_link, file):
    """
    download the pmc tar file to destination file
    :param download_link: web link to download tar file
    :param file: file to write the tar file into
    :return: write/download tar file to file
    """
    response=requests.get(download_link, stream=True)
    response.raise_for_status()
    if response.status_code==200: #check get response, is there an error from server side is the link correct
        try:
            with open(file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192): #1MB chunk downloads
                    f.write(chunk)
            return None
        except Exception as e:
            raise RuntimeError('Could not download tar file: {}'.format(e)) from e
    else:
        return response.raise_for_status()

