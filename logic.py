
class Lock:
    def __init__(self, number, lock_type, length, finish, quantity, pinning):
        self.number = number
        self.lock_type = lock_type
        self.length = length
        self.finish = finish
        self.quantity = quantity
        self.pinning = pinning

    def get_number(self):
        return self.number

    def get_lock_type(self):
        return self.lock_type

    def get_length(self):
        return self.length

    def get_finish(self):
        return self.finish

    def get_quantity(self):
        return self.quantity

    def get_pinning(self):
        return self.pinning


lock_data = [  {'number': '12345', 'type': 'Deadbolt', 'length': '2-1/2"', 'finish': 'Brass', 'quantity': 10, 'pinning': [1, 2, 3, 4]},
  {'number': '67890', 'type': 'Padlock', 'length': '1-3/4"', 'finish': 'Stainless Steel', 'quantity': 5, 'pinning': [3, 4, 5, 6]},
  {'number': '23456', 'type': 'Deadbolt', 'length': '2-3/4"', 'finish': 'Bronze', 'quantity': 15, 'pinning': [2, 3, 4, 5]},
]

locks = []
for lock_dict in lock_data:
  lock = Lock(lock_dict['number'], lock_dict['type'], lock_dict['length'], lock_dict['finish'], lock_dict['quantity'], lock_dict['pinning'])
  locks.append(lock)


def get_locks(text):
    return locks