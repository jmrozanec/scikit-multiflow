from skmultiflow.data.observer.event_observer import EventObserver
import numpy as np

class EvaluationEventObserver(EventObserver):
    """ EvaluationEventObserver class.
    """

    def __init__(self, algorithm, train_eval_trigger, results_observer):
        """ EvaluationEventObserver class constructor."""
        super().__init__()
        self.algorithm = algorithm
        self.train_eval_trigger = train_eval_trigger
        self.results_observer = results_observer
        self.y_true_buffer = []
        self.y_pred_buffer = []
        self.x_buffer = []

    def update(self, event):
        if event is not None:
            algorithm_type = self.algorithm.algorithm_type()
            x = event['X']
            y_true = None
            if algorithm_type == 'CLASSIFICATION' or algorithm_type == 'REGRESSION':
                y_true = event['y']

            self.train_eval_trigger.update(event)

            if self.train_eval_trigger.shall_predict(event):
                y_pred = self.algorithm.predict(x)
                self.y_true_buffer.append(y_true)
                self.y_pred_buffer.append(y_pred)

            if self.train_eval_trigger.shall_fit(event):
                print("Will report? {}".format(len(self.y_true_buffer)))
                if len(self.y_true_buffer)>0:
                    self.results_observer.report(self.y_pred_buffer, self.y_true_buffer)
                    self.y_pred_buffer = []
                    self.y_true_buffer = []

                x_array = np.array(x)
                x_array = x_array.reshape(1, x_array.shape[0])
                y_array = np.array(y_true)
                #y_array = y_array.reshape(1, 1)

                print("Shapes are: {}->{}".format(x_array.shape, y_array.shape))
                self.algorithm.partial_fit(x_array, y_array, [0, 1, 2])
