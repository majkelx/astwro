

class Individual(object):

    genome = None
    __score = None

    def __init__(self, score_function=None):
        """
        :param ScoreFunction score_function:
        """
        self.score_function = score_function

    @property
    def score(self):
        if self.__score is None:
            self.__score = self.score_function.calc(individual=self)
        return self.__score
