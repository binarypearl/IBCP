import random

class number_guesser_engine:
    def __init__(self):
        self.__min = 1
        self.__max = 100
        self.__magic_number = 0
        self.__user_guess_count = 0
        self.__current_min = 1
        self.__current_max = 100

    def initialize_game(self):
        self.__min = 1
        self.__max = 100
        self.__user_guess_count = 0
        self.__current_min = self.__current_min
        self.__current_max = self.__current_max
        self.set_magic_number()

    def set_magic_number(self):
        self.__magic_number = random.randint(1,101)

    def get_magic_number(self):
        return (self.__magic_number)

    def increase_user_guess_count(self, count):
        self.__user_guess_count += count

    def get_user_guess_count(self):
        return (self.__user_guess_count)

    def set_current_min(self, user_min):
        self.__current_min = user_min

    def get_current_min(self):
        return (self.__current_min)

    def set_current_max(self, user_max):
        self.__current_max = user_max

    def get_current_max(self):
        return (self.__current_max)

    def guess_a_number(self, too_low_or_too_high, cur_min, cur_max):
        guess = "oops"

        if too_low_or_too_high == "initial_guess":
            guess = 50

        elif too_low_or_too_high == "too_high":
            guess = ((cur_max - cur_min) // 2) + cur_min

            print ("too high so guess = " + str(cur_max) + " and we divide that by 2 to give us: " + str(guess))

        elif too_low_or_too_high == "too_low":
            guess = ((cur_max - cur_min) // 2) + cur_min

            print ("too low so guess = " + str(cur_max) + " minus " + str(cur_min) + " and we divide that by 2 and add back in cur_min to give us: " + str(guess))

        return (guess)
