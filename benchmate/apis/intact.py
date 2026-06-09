import json
import requests

from benchmate.apis.utils import api_call, ApiCall

class IntAct:
    call_class=ApiCall

    def __init__(self, page=0, page_size=100):
        self.url = 'https://www.ebi.ac.uk/intact/ws/interaction/findInteractions/{}?page={}&pageSize={}'
        self.page = page
        self.page_size = page_size
        self.init_kwargs={"page":page, "page_size":page_size}

    def _search(self, ebi_id, page):
        """
        Search for interactions in IntAct database.
        :param ebi_id: The EBI ID to search for.
        :return: A list of interactions.
        """

        intact_response = requests.get(self.url.format(ebi_id, page, self.page_size))
        intact_response.raise_for_status()
        intact_response = json.loads(intact_response.content.decode())
        interactions = []
        for ints in intact_response["content"]:
            interaction = {"idA": ints["idA"], "idB": ints["idB"], "taxidA": ints["taxIdA"], "taxidB": ints["taxIdB"],
                           "experimental_role_A": ints["experimentalRoleA"],
                           "experimental_role_B": ints["experimentalRoleB"], "stoichiometry_A": ints["stoichiometryA"],
                           "stoichiometry_B": ints["stoichiometryB"], "detection_method": ints["detectionMethod"],
                           "annotations": "\n".join(item for item in ints["allAnnotations"]),
                           "is_negative": ints["negative"], "affected_by_mutation": ints["affectedByMutation"],
                           "pubmed_id": ints["publicationPubmedIdentifier"], "score": ints["intactMiscore"], }

            interactions.append(interaction)
        if intact_response["last"]:
            last_page = True
        else:
            last_page = False

        return interactions, last_page

    @api_call(lambda self: self.call_class)
    def search(self, ebi_id, page=0):
        """
        search intact database
        :param ebi_id: ebi
        :param page: which page to start from, this is more of a precaution for very large searches, if you lose connection you can
        resume from the last page you got data from, default 0
        :return: a dataframe of all interactions found
        """
        interactions, last_page = self._search(ebi_id, page)
        while not last_page:
            page = page + 1
            next_page_interactions, last_page = self._search(ebi_id, page)
            interactions.extend(next_page_interactions)
        return interactions