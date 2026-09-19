from abc import ABC, abstractmethod

# 1. Interface Strategy (Abstração)
class EstrategiaSaudacao(ABC):
    @abstractmethod
    def saudar(self, nome: str) -> str:
        pass

# 2. Estratégias Concretas
class SaudacaoBrasil(EstrategiaSaudacao):
    def saudar(self, nome: str) -> str:
        return f"Olá, {nome}!"

class SaudacaoUSA(EstrategiaSaudacao):
    def saudar(self, nome: str) -> str:
        return f"Hello, {nome}!"

# 3. Contexto (A classe que utiliza a estratégia)
class HelloWorld:
    def __init__(self, pais: str):
        self.estrategia = self._definir_estrategia(pais)

    def _definir_estrategia(self, pais: str) -> EstrategiaSaudacao:
        # Mapeia o parâmetro para a estratégia correspondente
        estrategias = {
            "BRZ": SaudacaoBrasil(),
            "USA": SaudacaoUSA()
        }
        
        # Retorna a estratégia correta ou levanta um erro se o país não for suportado
        if pais in estrategias:
            return estrategias[pais]
        raise ValueError(f"País '{pais}' não é suportado.")

    def executar(self, nome: str = "Mundo") -> str:
        return self.estrategia.saudar(nome)

# Exemplo de uso:
if __name__ == "__main__":
    # Testando a estratégia para o Brasil
    app_brz = HelloWorld(pais="BRZ")
    print(app_brz.executar("Carlos"))  # Saída: Olá, Carlos!

    # Testando a estratégia para os EUA
    app_usa = HelloWorld(pais="USA")
    print(app_usa.executar("John"))    # Saída: Hello, John!
