#TODO GetLastAttackTime() this will have minor impacts
# TODO have a more general Unit that creep and hero inherit from as they share quite a few variables
class Hero(object):
    def __init__(self, data):
        self.name = data.name
        self.range = data.range
        self.attackspeed = data.attackspeed
        self.attackdamage = data.attackdamage
        self.movespeed = data.movespeed


class Creep():
    # TODO need to add whether its being attacked or not
    def __init__(self, data):
        self.health = data.health


class LaneCreep(Creep):
    """
    ranged: True if ranged creep. False otherwise
        - ranged creeps have 0 armour. melee 2.
    """
    def __init__(self, data):
        self.ranged = (data.armour == 0)
        super(Creep, self).__init__(data)


class NeutralCreep(Creep):
    def __init__(self, data):
        self.armour = data.armour
        self.attackdamage = data.attackdamage
        self.attackspeed = data.attackspeed
        super(Creep, self).__init__(data)