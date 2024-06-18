import numpy as np


class evaluator():
    def __init__(self, groundTruths, predictions):
        self.groundTruths = groundTruths
        self.predictions = predictions
        pass

    def _accuracy(self, classHit):
        length = np.sum(classHit)
        accuracy = np.round((classHit / length) * 100, 2)
        accuracy[1:] = np.add.accumulate(accuracy[1:])
        return accuracy, length

    def run(self):
        evaluations = []

        # Accuracy
        evaluation = {
            'metrics': 'Accuracy',
            'detail': {},
            'mean': {}
        }
        classHitTable = {}
        topLength = 0
        for prediction in self.predictions:
            hit = 0
            key = prediction['path']
            truth = self.groundTruths[key] if key in self.groundTruths else ''
            for index in prediction['predicts']:
                predict = prediction['predicts'][index]
                if predict['class'] == truth:
                    hit = int(index)
                    break
            prediction['evaluate'] = {
                'hit': hit if hit > 0 else -1,
                'truth': truth
            }
            try:
                classHitTable[truth][hit] += 1
            except:
                topLength = len(prediction['predicts']) + 1
                classHitTable[truth] = np.zeros(topLength)
                classHitTable[truth][hit] += 1

        # count mean accuracy
        meanAccuracy = np.zeros(topLength)
        for tclass in classHitTable:
            classHit = classHitTable[tclass]
            accuracy, length = self._accuracy(classHit)
            meanAccuracy = meanAccuracy + accuracy
            classEval = dict([['top' + str(i if i > 0 else -1), str(accuracy[i]) + '%'] for i in range(topLength)])
            classEval['length'] = int(length)
            evaluation['detail'][tclass] = classEval
        meanAccuracy = np.round(meanAccuracy / (len(classHitTable) + 0.000001), 2)
        evaluation['mean'] = dict(
            [['top' + str(i if i > 0 else -1), str(meanAccuracy[i]) + '%'] for i in range(topLength)])

        evaluations.append(evaluation)
        return evaluations, self.predictions