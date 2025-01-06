# utils/macro.py
import pandas as pd
import logging

def process_fed_funds_rate(filepath, logger):
    try:
        ff_data = pd.read_csv(filepath)
        # Implementar processamento conforme necessário
        logger.info(f"Dados da FFR carregados a partir de {filepath}")
        return ff_data
    except Exception as e:
        logger.error(f"Erro ao processar FFR: {e}")
        raise