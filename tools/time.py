import datetime

from chain.params import BLOCK_TIME

current_test_time = 0
is_test_time = False

class Time:
    @staticmethod
    def set_current_time(time):
        global current_test_time
        current_test_time = time

    @staticmethod
    def use_test_time():
        global is_test_time
        is_test_time = True
    
    @staticmethod
    def advance_time(seconds):
        global current_test_time
        current_test_time += seconds

    @staticmethod
    def advance_to_next_timeslot():
        global current_test_time
        current_test_time += BLOCK_TIME
     
    @staticmethod
    def get_current_time():
        global is_test_time
        if is_test_time:        
            global current_test_time
            return current_test_time
        else:
            return int(datetime.datetime.now().timestamp())