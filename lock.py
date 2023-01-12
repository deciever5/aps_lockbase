class Lock:
    def __init__(self, number, lock_type, length, finish, profile, quantity, pinning, body_pins, side_pins, ext_pins,
                 pin_sum):
        self._number = number
        self._lock_type = lock_type
        self._length = length
        self._finish = finish
        self._profile = profile
        self._quantity = quantity
        self._pinning = pinning
        self._body_pins = body_pins
        self._side_pins = side_pins
        self._ext_pin = ext_pins
        self._pin_sum = pin_sum

    """def __str__(self): return f'Number: {self._number}, Lock Type: {self._lock_type}, Length: {self._length}, 
    Finish: {self._finish}, ' \ f'Profile: {self._profile}, Quantity: {self._quantity}, Body Pins: {self._body_pins}, 
    Side Pins: {self._side_pins}, Extension Pins: {self._ext_pin} ' """

    def __str__(self):
        return f'Number: {self._number}, Body Pins: {self._body_pins}, Side Pins: {self._side_pins}, Extension Pins: {self._ext_pin} '

    @property
    def number(self):
        return self._number

    @property
    def lock_type(self):
        return self._lock_type

    @property
    def length(self):
        return self._length

    @property
    def finish(self):
        return self._finish

    @property
    def profile(self):
        return self._profile

    @property
    def quantity(self):
        return self._quantity

    @property
    def pinning(self):
        return self._pinning

    @property
    def body_pins(self):
        return self._body_pins

    @property
    def side_pins(self):
        return self._side_pins

    @property
    def pin(self):
        return self._ext_pin


def create_locklist(df):
    lock_list = []
    for i in range(df.shape[0]):
        number = df.iloc[i, 6]
        lock_type = df.iloc[i, 7]
        length = df.iloc[i, 2]
        finish = df.iloc[i, 1]
        profile = df.iloc[i, 4]
        quantity = df.iloc[i, 5]
        pinning = str(df.iloc[i, 3]).replace('\r', '').split('\n')
        body_pins = pinning[0].split(' ')[0] if pinning[0].split(' ')[0].isnumeric() else None
        side_pins = pinning[0].split(' ')[1] if pinning[0].split(' ')[0].isnumeric() else None
        ext_pin = count_ext_pins(pinning[1:], body_pins) if len(pinning) > 1 else None
        pin_sum = None

        lock = Lock(number, lock_type, length, finish, profile, quantity, pinning, body_pins, side_pins, ext_pin,
                    pin_sum)
        lock_list.append(lock)

    """for lock in lock_list:
        print(lock)"""

    return lock_list


def count_ext_pins(ext_pins, body_pins):
    body_pins_list = [i for i in body_pins]
    ext_pins_list = [[x.replace("a", "10").replace("b", "11").replace(" ", "0") for x in k] for k in
                     [list(j) for j in [k for k in ext_pins]]]

    print(body_pins_list, ext_pins_list)

    return ext_pins_list
