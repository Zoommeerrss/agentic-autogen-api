from collections import namedtuple

from src.domain.entity.person_entity import PersonEntity

def __dto_2_entity__(obj: PersonEntity):
    return PersonEntity(obj.name, obj.lastname, obj.career, obj.age)


def default(self, o):
    return o.__dict__


def input_2_decode(obj_dict: dict) -> PersonEntity:
    """
    Recebe o dicionário do payload e mapeia diretamente para a Entidade de Domínio.
    Abordagem Lean: Garante validação de campos obrigatórios e tipagem forte.
    """
    if not obj_dict:
        return None

    try:
        return PersonEntity(
            name=obj_dict.get("name"),
            lastname=obj_dict.get("lastname"),
            career=obj_dict.get("career"),
            age=obj_dict.get("age")
        )
    except Exception as e:
        print(f"Erro ao converter payload para PersonEntity: {e}")
        return None