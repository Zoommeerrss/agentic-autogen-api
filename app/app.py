import sys
import os
import json

from src.domain.converter.person_converter import input_2_decode

def lambda_handler(event, context):
    """Sample pure Lambda function"""
    print("lambda_handler init")

    try:
        # 2. Identificação do Payload
        if "data" in event:
            payload = event["data"]
        elif "body" in event:
            payload = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            payload = event

        print(f"DEBUG - Payload identificado: {payload}")

        # 3. Desserialização e criação do objeto person
        person = input_2_decode(payload)
        print(f"DEBUG - Person gerado: {person}")

        if person:
            nome = getattr(person, 'name', 'Atributo name nao encontrado')
            print("evento recebido: ", nome)

        print("lambda_handler end")

        # O bloco return DEVE estar neste exato nível de indentação (alinhado ao try)
        return {
            "statusCode": 200,
            "body": json.dumps({"data": person, }),
        }

    except Exception as e:
        print(f"ERRO CRÍTICO NA EXECUÇÃO: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

# Certifique-se de que o bloco abaixo está totalmente encostado na margem esquerda (sem espaços antes)
if __name__ == "__main__":
    payload_teste = {
        "data": {
            "name": "Alex",
            "lastname": "Rider",
            "career": "Engineer",
            "age": 30
        }
    }

    resultado = lambda_handler(payload_teste, None)
    print("\nResultado final da execução:")
    print(json.dumps(resultado, indent=4))
