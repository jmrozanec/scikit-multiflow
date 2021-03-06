from abc import ABCMeta, abstractmethod


class TrainEvalTrigger(metaclass=ABCMeta):
    """ TrainEvalTrigger class.

    This abstract class defines the minimum requirements of a trigger.
    It provides an interface to define criteria when data shall be fitted and evaluated.

    Raises
    ------
    NotImplementedError: This is an abstract class.

    """

    @abstractmethod
    def update(self, event):
        """
        This method aims to store the event, so that can be used to fit or predict
        :param event:
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def shall_predict(self):
        raise NotImplementedError

    @abstractmethod
    def shall_buffer(self):
        raise NotImplementedError

    @abstractmethod
    def instances_to_fit(self, t, x, y):
        raise NotImplementedError

    @abstractmethod
    def remaining_buffer(self, t, x, y):
        raise NotImplementedError


class PrequentialTrigger(TrainEvalTrigger):

    def __init__(self, n_wait_to_fit):
        self.first_time_wait = n_wait_to_fit
        self.first_time_wait_counter = 0

    def update(self, event):
        if self.first_time_wait_counter <= self.first_time_wait:
            self.first_time_wait_counter += 1

    def shall_predict(self):
        if self.first_time_wait_counter <= self.first_time_wait:
            return False
        return True

    def shall_buffer(self):
        return True

    def instances_to_fit(self, t, x, y):
        return x, y

    def remaining_buffer(self, t, x, y):
        return [], [], []


class TimeBasedHoldoutTrigger(TrainEvalTrigger):

    def __init__(self, initial_time_window, wait_to_test_time_window, test_time_window, get_event_time):
        self.initial_time_window = initial_time_window
        self.wait_to_test_time_window = wait_to_test_time_window
        self.test_time_window = test_time_window
        self.get_event_time = get_event_time

        self.test_mode = False
        self.reference_time = None
        self.target_window = self.initial_time_window

    def update(self, event):
        event_time = self.get_event_time(event)
        if self.reference_time is None:
            self.reference_time = event_time

        time_between = event_time - self.reference_time
        if time_between > self.target_window:
            self.reference_time = event_time
            print("Switched to reference time: {}".format(self.reference_time))
            self.test_mode = not self.test_mode
            if self.test_mode:
                self.target_window = self.test_time_window
            else:
                self.target_window = self.wait_to_test_time_window

    def shall_buffer(self):
        return not self.test_mode

    def shall_predict(self):
        return self.test_mode

    def instances_to_fit(self, t, x, y):
        return x, y

    def remaining_buffer(self, t, x, y):
        return [], [], []


class QuantityBasedHoldoutTrigger(TrainEvalTrigger):

    #TODO: support dynamic and static test set: we support it considering the report evaluation policy
    def __init__(self, first_time_wait, n_wait_to_test, test_size):
        self.first_time_wait = max(first_time_wait, n_wait_to_test)
        self.n_wait_to_test = n_wait_to_test
        self.test_size = test_size
        self.test_mode = False
        self.events_counter = 0
        self.events_target = self.first_time_wait

    def update(self, event):
        if self.events_counter == self.events_target:
            self.test_mode = not self.test_mode
            self.events_counter = 0
            if self.test_mode:
                self.events_target = self.test_size
            else:
                self.events_target = self.n_wait_to_test

        if self.events_counter < self.events_target:
            self.events_counter += 1


    def shall_buffer(self):
        return not self.test_mode

    def shall_predict(self):
        return self.test_mode

    def instances_to_fit(self, t, x, y):
        return x, y

    def remaining_buffer(self, t, x, y):
        return [], [], []


class TimeBasedCrossvalidationTrigger(TrainEvalTrigger):

    def __init__(self, initial_time_window, wait_to_test_time_window, test_time_window, get_event_time):
        self.initial_time_window = initial_time_window
        self.wait_to_test_time_window = wait_to_test_time_window
        self.test_time_window = test_time_window
        self.get_event_time = get_event_time

        self.reference_time = None
        self.completed_initial_time_window = False
        self.fit_buffered_instances = False
        self.remaining_buffer_checked = False
        self.target_window = self.initial_time_window

    def update(self, event):
        event_time = self.get_event_time(event)
        if self.reference_time is None:
            self.reference_time = event_time

        time_between = event_time - self.reference_time
        if time_between > self.target_window:
            self.reference_time = event_time
            self.completed_initial_time_window = True
            self.fit_buffered_instances = True
            self.remaining_buffer_checked = False
            self.target_window = self.test_time_window

    def shall_buffer(self):
        return True

    def shall_predict(self):
        return self.completed_initial_time_window

    def instances_to_fit(self, t, x, y):
        if not self.completed_initial_time_window:
            return x, y
        else:
            if self.fit_buffered_instances:
                self.fit_buffered_instances = False
                return x, y
        return [], []

    def remaining_buffer(self, t, x, y):
        if not self.completed_initial_time_window:
            return [], [], []
        else:
            if not self.remaining_buffer_checked:
                self.remaining_buffer_checked = True
                return [], [], []
        return t, x, y



# TODO: implement prequential delayed
