class PersonEntity(object):
    name = ""
    lastname = ""
    career = ""
    age = 0

    def __init__(self, name, lastname, career, age):
        # body of the constructor
        self.name = name
        self.lastname = lastname
        self.career = career
        self.age = age

    def to_string(self):
        return "Person name %s, lastname %s, career %s , age %s" % (self.name, self.lastname, self.career, self.age)
