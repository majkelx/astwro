from .Individual import Individual

class ScoreFunction(object):

    def calc(self, individual):
        """
        Calculates score of individual. To be overridden.
        :param Individual individual:
        :return: float
        """
        return 0