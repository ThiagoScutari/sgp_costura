import math

def calculate_tl(operators: float, pulse_duration: int, tp_ajustado: float) -> int:
    """
    Calcula o Tamanho do Lote (TL) baseado na capacidade da célula.
    
    Fórmula: floor((Operators * pulse_duration) / TP)
    
    Args:
        operators: Número de operadores na célula.
        pulse_duration: Duração do pulso em minutos (ex: 30, 60).
        tp_ajustado: Tempo padrão ajustado da peça (em minutos).
        
    Returns:
        int: Quantidade de peças por lote (arredondado para baixo).
    """
    if tp_ajustado <= 0:
        return 0
    
    raw_tl = (operators * pulse_duration) / tp_ajustado
    return math.floor(raw_tl)
