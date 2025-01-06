# projeto_ml_trade/strategies/double_bottom_rsi_strategy.py
from datetime import datetime
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
from .base import BaseStrategy
from .trend_analysis import TrendAnalysisStrategy
import logging

logger = logging.getLogger(__name__)

class DoubleBottomRSIStrategy(BaseStrategy):
    """
    Estratégia que detecta o padrão de Double Bottom com:
      1. Detecção dos dois fundos com divergência de RSI:
         - RSI entre 25-50 para ambos os fundos
         - RSI do segundo fundo maior que o primeiro (divergência)
      2. Confirmação do rompimento da 'neckline' (máxima intermediária).
      3. Ajuste automático de parâmetros ao timeframe (ex.: lookback, tolerância).
      4. Gerenciamento de risco baseado na tendência:
         - Downtrend: RR 6.0, SL 3% (mais agressivo)
         - Uptrend: RR 1.5, SL 2% (mais conservador)
    """
    def __init__(
        self, 
        df: pd.DataFrame,
        rsi_period: int = 14,
        rsi_oversold: int = 25,  # Ajustado para 25-50
        min_separation_candles: int = 3,   # Mínimo de candles entre fundos (3-7)
        default_pattern_lookback: int = 30,
        default_price_tolerance: float = 0.08,  # Aumentado para 8%
        volume_ratio: float = 0.6,  # Reduzido para 60%
        default_risk_reward: float = 1.5,
        default_stop_loss_pct: float = 0.02,
        downtrend_risk_reward: float = 6.0,
        downtrend_stop_loss_pct: float = 0.03,
        # Parâmetros do backtester (opcionais)
        risk_reward: float = None,
        stop_loss_pct: float = None
    ):
        """
        Args:
            df: DataFrame com dados OHLCV e indicadores, ordenado por timestamp
            rsi_period: Período para cálculo do RSI
            rsi_oversold: Nível considerado de sobrevenda (25-50)
            min_separation_candles: Mínimo de candles entre o 1º e 2º fundo (3-7)
            default_pattern_lookback: Lookback padrão para detecção do padrão
            default_price_tolerance: Tolerância de preço para considerar fundos 'similares'
            volume_ratio: Razão mínima de volume do segundo fundo em relação ao primeiro
            risk_reward: (opcional) Risk/reward do backtester
            stop_loss_pct: (opcional) Stop loss do backtester
        """
        super().__init__(df)
        
        # Detectar timeframe a partir de 2 candles consecutivos
        self.timeframe = self.detect_timeframe()
        
        # Ajustar parâmetros sensíveis com base no timeframe
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.min_separation_candles = int(min_separation_candles)
        
        # Usamos um lookback diferente dependendo do timeframe (exemplo simples)
        # Você pode criar uma lógica mais elaborada se preferir
        self.pattern_lookback = int(self.adjust_parameter_by_timeframe(
            default_value=default_pattern_lookback,
            factor_map={
                '1m': 0.5,
                '5m': 0.8,
                '1h': 1.0,
                '4h': 1.5,
                '1d': 2.0
            }
        ))
        
        self.price_tolerance = self.adjust_parameter_by_timeframe(
            default_value=default_price_tolerance,
            factor_map={
                '1m': 0.7,
                '5m': 0.8,
                '1h': 1.0,
                '4h': 1.2,
                '1d': 1.5
            }
        )
        
        self.volume_ratio = volume_ratio
        
        # Risk management parameters - usar valores do backtester se fornecidos
        self.default_risk_reward = risk_reward if risk_reward is not None else default_risk_reward
        self.default_stop_loss_pct = stop_loss_pct if stop_loss_pct is not None else default_stop_loss_pct
        self.downtrend_risk_reward = risk_reward * 4 if risk_reward is not None else downtrend_risk_reward
        self.downtrend_stop_loss_pct = stop_loss_pct if stop_loss_pct is not None else downtrend_stop_loss_pct
        
        # Initialize trend analyzer
        self.trend_analyzer = TrendAnalysisStrategy()
        
        # Log dos parâmetros de risco e configuração
        logger.info("Strategy parameters initialized:")
        logger.info(f"RSI range: 25-50")
        logger.info(f"Price tolerance: {self.price_tolerance:.1%}")
        logger.info(f"Volume ratio: {self.volume_ratio:.1%}")
        logger.info(f"Risk parameters:")
        logger.info(f"Default RR: {self.default_risk_reward}, SL: {self.default_stop_loss_pct:.1%}")
        logger.info(f"Downtrend RR: {self.downtrend_risk_reward}, SL: {self.downtrend_stop_loss_pct:.1%}")

    def detect_timeframe(self) -> str:
        """
        Tenta inferir o timeframe analisando a diferença de tempo
        entre os dois primeiros candles do DataFrame.
        
        Retorna algo como: '1m', '5m', '1h', '4h', '1d', etc.
        Caso não consiga identificar, retorna 'desconhecido'.
        """
        if len(self.df) < 2:
            return 'desconhecido'
        
        time_delta = self.df['timestamp'].iloc[1] - self.df['timestamp'].iloc[0]
        minutes = time_delta.total_seconds() / 60
        
        if minutes <= 1.1:
            return '1m'
        elif minutes <= 5.5:
            return '5m'
        elif minutes <= 60:
            return '1h'
        elif minutes <= 240:
            return '4h'
        elif minutes <= 1440:
            return '1d'
        else:
            return 'desconhecido'
    
    def adjust_parameter_by_timeframe(self, default_value: float, factor_map: Dict[str, float]) -> float:
        """
        Ajusta um parâmetro baseando-se em um dicionário de fatores por timeframe.
        Se não encontrar o timeframe, retorna o valor default.
        
        Args:
            default_value: Valor padrão do parâmetro
            factor_map: Mapeia timeframe -> fator multiplicador
        
        Returns:
            float: Valor ajustado
        """
        factor = factor_map.get(self.timeframe, 1.0)
        return default_value * factor
    
    def find_local_minima(self, window: pd.DataFrame) -> List[Tuple[datetime, float]]:
        """
        Encontra mínimos locais em uma janela de preços usando TrendAnalysis.
        
        Returns:
            List[Tuple[datetime, float]]: (timestamp, preço) dos mínimos locais
        """
        signals = self.trend_analyzer.generate_signals(window)
        minima = []
        for signal in signals:
            if signal['type'] == 'low':
                minima.append((signal['timestamp'], signal['price']))
        return minima

    def detect_double_bottom_candidates(self) -> List[Dict]:
        """
        Detecção inicial dos fundos duplos:
          1. Encontra dois fundos próximos (preços similares).
          2. Verifica condições de RSI:
             - RSI entre 25-50 para ambos os fundos
             - RSI do segundo fundo deve ser maior (divergência bullish)
          3. Verifica volume do segundo fundo em relação ao primeiro.
          4. Determina parâmetros de risco baseado na tendência.
          
        OBS: Aqui ainda não confirma o rompimento da neckline.
        
        Returns:
            List[Dict]: Lista de candidatos a double bottom (sem confirmação de breakout).
            Cada candidato inclui:
            - timestamps e preços dos dois fundos
            - força do sinal preliminar
            - metadata com métricas e parâmetros de risco
        """
        candidates = []
        
        # Detectar tendência usando TrendAnalysisStrategy
        trend_signals = self.trend_analyzer.generate_signals(self.df)
        trend = pd.Series(0, index=self.df.index)
        for signal in trend_signals:
            if signal['type'] == 'uptrend':
                trend[signal['timestamp']] = 1
            elif signal['type'] == 'downtrend':
                trend[signal['timestamp']] = -1
        
        for i in range(self.pattern_lookback, len(self.df)):
            # Obter tendência atual para gerenciamento de risco
            if i > 0:
                idx = self.df.index[i-1]
                current_trend = trend[idx]
            else:
                current_trend = 0
            
            # Criar janela deslizante
            window = self.df.iloc[i-self.pattern_lookback:i+1]
            minima = self.find_local_minima(window)
            if len(minima) < 2:
                continue
            
            # Pega os dois últimos fundos
            last_two = minima[-2:]
            time1, price1 = last_two[0]
            time2, price2 = last_two[1]
            
            # Verifica se há um mínimo de candles de separação (3-7)
            idx_time1 = self.df.index.get_loc(time1)
            idx_time2 = self.df.index.get_loc(time2)
            if (idx_time2 - idx_time1) < self.min_separation_candles:
                continue
            
            # Verifica se os preços são similares (dentro de price_tolerance)
            price_diff = abs(price2 - price1) / price1
            if price_diff > self.price_tolerance:
                continue
            
            # Verifica RSI em zona de sobrevenda (25-50)
            rsi1 = self.df.loc[time1, 'rsi']
            rsi2 = self.df.loc[time2, 'rsi']
            if not (25 <= rsi1 <= 50 and 25 <= rsi2 <= 50):
                continue
                
            # Divergência bullish clássica: segundo fundo <= preço do primeiro
            # e RSI do segundo > RSI do primeiro
            if not (price2 <= price1 and rsi2 > rsi1):
                continue
            
            # Verifica volume do segundo fundo em relação ao primeiro
            vol1 = self.df.loc[time1, 'volume']
            vol2 = self.df.loc[time2, 'volume']
            if vol2 < vol1 * self.volume_ratio:
                continue
            
            # Determinar parâmetros de risco baseado na tendência
            if current_trend == -1:  # Downtrend - mais agressivo
                risk_reward = self.downtrend_risk_reward  # 6.0
                stop_loss_pct = self.downtrend_stop_loss_pct  # 3%
            else:  # Uptrend - mais conservador
                risk_reward = self.default_risk_reward  # 1.5
                stop_loss_pct = self.default_stop_loss_pct  # 2%
            
            # Calcula força do sinal preliminar (sem breakout)
            rsi_diff = (rsi2 - rsi1) / max(rsi1, 1e-6)
            vol_ratio = vol2 / max(vol1, 1e-6)
            signal_strength = min((rsi_diff * vol_ratio) / 2, 1.0)
            
            # Armazena candidato
            candidates.append({
                'timestamp': self.df.index[i],  # Fecha a janela
                'first_bottom':  (time1, price1),
                'second_bottom': (time2, price2),
                'direction': 'long',
                'strength_pre_breakout': signal_strength,
                'metadata': {
                    'price_diff': price_diff,
                    'volume_ratio': vol_ratio,
                    'rsi_divergence': rsi2 - rsi1,
                    'trend': trend[self.df.index[i-1]],
                    'risk_reward': risk_reward,
                    'stop_loss_pct': stop_loss_pct
                }
            })
        
        return candidates
    
    def confirm_breakout(self, candidate: Dict) -> Dict:
        """
        Confirma o rompimento da 'neckline' (máxima entre os dois fundos).
        
        Processo de confirmação:
        1. Identifica a neckline (máxima entre os dois fundos)
        2. Verifica se houve fechamento acima da neckline
        3. Analisa volume do breakout:
           - Volume > 120% da média: força total (1.0)
           - Volume <= 120% da média: força reduzida (0.7)
        4. Atualiza força do sinal baseado no volume
        
        Returns:
            Dict: Candidato atualizado com:
                - confirmed: bool indicando se houve confirmação
                - strength: força final do sinal (0.0 a 1.0)
                - neckline: preço da neckline
                - breakout_timestamp: momento do rompimento
                - metadata atualizado com volumes
        """
        # Pega os timestamps de cada fundo
        time1, price1 = candidate['first_bottom']
        time2, price2 = candidate['second_bottom']
        
        # Calcula a 'neckline' = máxima entre os dois fundos
        # Vamos achar o candle entre time1 e time2 que tenha a maior máxima
        idx1 = self.df.index.get_loc(time1)
        idx2 = self.df.index.get_loc(time2)
        if idx1 > idx2:
            idx1, idx2 = idx2, idx1
        
        window = self.df.iloc[idx1:idx2+1]
        neckline = window['high'].max()
        
        # Confirma se o preço rompeu a neckline depois do segundo fundo
        # Procuramos no DF a partir do idx2 + 1 até, digamos, idx2 + X
        # (Você pode decidir quantos candles olhar para ver se houve rompimento)
        confirm_window = self.df.iloc[idx2+1 : idx2+int(self.pattern_lookback/3)]  # Janela proporcional ao lookback
        breakout_candle = confirm_window[confirm_window['close'] > neckline]
        
        if breakout_candle.empty:
            # Não houve rompimento
            candidate['confirmed'] = False
            candidate['strength'] = candidate['strength_pre_breakout'] * 0.5  # Penaliza força
            return candidate
        
        # Se houve rompimento, verificar volume
        # Exemplo: pegamos o candle exato do breakout (primeiro que rompeu)
        breakout_idx = idx2 + 1 + len(confirm_window[:confirm_window.index.get_loc(breakout_candle.index[0])])
        if breakout_idx >= len(self.df):
            # Se o índice estiver fora dos limites, não confirmar o padrão
            candidate['confirmed'] = False
            candidate['strength'] = candidate['strength_pre_breakout'] * 0.5  # Penaliza força
            return candidate
            
        breakout_volume = self.df.iloc[breakout_idx]['volume']
        
        # Comparamos breakout_volume com média de volume da janela do 2º fundo
        vol_window_lookback = int(self.pattern_lookback/3)  # Janela proporcional ao lookback
        vol_window = self.df.iloc[max(0, breakout_idx - vol_window_lookback):breakout_idx]
        avg_vol = vol_window['volume'].mean() if len(vol_window) else breakout_volume
        
        if breakout_volume > avg_vol * 1.2:
            # Se houve volume pelo menos 20% maior que a média
            volume_confirmation_strength = 1.0
        else:
            volume_confirmation_strength = 0.7  # Valor arbitrário (pode ajustar conforme o caso)
        
        # Força final do sinal
        final_strength = candidate['strength_pre_breakout'] * volume_confirmation_strength
        final_strength = min(final_strength, 1.0)
        
        candidate['confirmed'] = True
        candidate['neckline'] = neckline
        candidate['breakout_timestamp'] = self.df.index[breakout_idx]
        candidate['strength'] = final_strength
        candidate['metadata']['breakout_volume'] = breakout_volume
        candidate['metadata']['avg_volume_before_breakout'] = avg_vol
        
        return candidate
    
    def generate_signals(self, progress_callback=None) -> List[Dict]:
        """
        Gera sinais de trading para o padrão Double Bottom.
        
        Processo:
        1. Identifica candidatos a Double Bottom:
           - Dois fundos com preços similares
           - RSI entre 25-50 para ambos os fundos
           - Divergência bullish no RSI
           - Volume adequado no segundo fundo
        
        2. Confirma rompimento da neckline:
           - Fechamento acima da máxima entre os fundos
           - Análise do volume no breakout
           - Cálculo da força do sinal
        
        3. Gera sinais finais:
           - Apenas para padrões confirmados
           - Inclui parâmetros de risco baseados na tendência
           - Evita sinais duplicados em intervalo curto
        
        Args:
            progress_callback: Opcional. Função para reportar progresso da análise.
                             Recebe (porcentagem, timestamp, mensagem).
        
        Returns:
            List[Dict]: Lista de sinais gerados, cada um contendo:
                - timestamp e preço do breaktest
                - direção do trade (sempre 'long')
                - força do sinal (0.0 a 1.0)
                - metadata com detalhes do padrão e risco
        """
        # 1. Detectar candidatos
        total_candles = len(self.df)
        candidates = []
        
        # Detectar tendência usando TrendAnalysisStrategy
        trend_signals = self.trend_analyzer.generate_signals(self.df)
        trend = pd.Series(0, index=self.df.index)
        for signal in trend_signals:
            if signal['type'] == 'uptrend':
                trend[signal['timestamp']] = 1
            elif signal['type'] == 'downtrend':
                trend[signal['timestamp']] = -1
        
        for i in range(self.pattern_lookback, total_candles):
            # Atualizar progresso mais frequentemente
            if progress_callback and i % 50 == 0:  # A cada 50 candles
                progress = (i / total_candles) * 100
                current_timestamp = self.df.iloc[i]['timestamp']
                progress_callback(progress, current_timestamp, {
                    'message': 'Procurando sinais...',
                    'total_candles': total_candles,
                    'processed_candles': i,
                    'current_timestamp': current_timestamp
                })
            
            # Obter tendência atual para gerenciamento de risco
            if i > 0:
                idx = self.df.index[i-1]
                current_trend = trend[idx]
            else:
                current_trend = 0
            
            # Criar janela deslizante
            window = self.df.iloc[i-self.pattern_lookback:i+1]
            minima = self.find_local_minima(window)
            if len(minima) < 2:
                continue
            
            # Pega os dois últimos fundos
            last_two = minima[-2:]
            time1, price1 = last_two[0]
            time2, price2 = last_two[1]
            
            # Verifica se há um mínimo de candles de separação (3-7)
            idx_time1 = self.df.index.get_loc(time1)
            idx_time2 = self.df.index.get_loc(time2)
            if (idx_time2 - idx_time1) < self.min_separation_candles:
                continue
            
            # Verifica se os preços são similares (dentro de price_tolerance)
            price_diff = abs(price2 - price1) / price1
            if price_diff > self.price_tolerance:
                continue
            
            # Verifica RSI em zona de sobrevenda (25-50)
            rsi1 = self.df.loc[time1, 'rsi']
            rsi2 = self.df.loc[time2, 'rsi']
            if not (25 <= rsi1 <= 50 and 25 <= rsi2 <= 50):
                continue
                
            # Divergência bullish clássica: segundo fundo <= preço do primeiro
            # e RSI do segundo > RSI do primeiro
            if not (price2 <= price1 and rsi2 > rsi1):
                continue
            
            # Verifica volume do segundo fundo em relação ao primeiro
            vol1 = self.df.loc[time1, 'volume']
            vol2 = self.df.loc[time2, 'volume']
            if vol2 < vol1 * self.volume_ratio:
                continue
            
            # Determinar parâmetros de risco baseado na tendência
            if current_trend == -1:  # Downtrend - mais agressivo
                risk_reward = self.downtrend_risk_reward  # 6.0
                stop_loss_pct = self.downtrend_stop_loss_pct  # 3%
            else:  # Uptrend - mais conservador
                risk_reward = self.default_risk_reward  # 1.5
                stop_loss_pct = self.default_stop_loss_pct  # 2%
            
            # Calcula força do sinal preliminar (sem breakout)
            rsi_diff = (rsi2 - rsi1) / max(rsi1, 1e-6)
            vol_ratio = vol2 / max(vol1, 1e-6)
            signal_strength = min((rsi_diff * vol_ratio) / 2, 1.0)
            
            # Armazena candidato
            candidates.append({
                'timestamp': self.df.index[i],  # Fecha a janela
                'first_bottom':  (time1, price1),
                'second_bottom': (time2, price2),
                'direction': 'long',
                'strength_pre_breakout': signal_strength,
                'metadata': {
                    'price_diff': price_diff,
                    'volume_ratio': vol_ratio,
                    'rsi_divergence': rsi2 - rsi1,
                    'trend': trend[self.df.index[i-1]],
                    'risk_reward': risk_reward,
                    'stop_loss_pct': stop_loss_pct
                }
            })
        
        # 2. Confirmar cada candidato
        if progress_callback:
            last_timestamp = self.df.iloc[-1]['timestamp']
            progress_callback(90, last_timestamp, {
                'message': f'Confirmando {len(candidates)} sinais encontrados...',
                'total_trades': len(candidates),
                'current_timestamp': last_timestamp
            })
            
        confirmed_patterns = []
        for c in candidates:
            conf = self.confirm_breakout(c)
            if conf['confirmed']:
                confirmed_patterns.append(conf)
        
        # 3. Gera sinal final
        if progress_callback:
            last_timestamp = self.df.iloc[-1]['timestamp']
            progress_callback(95, last_timestamp, {
                'message': f'Gerando sinais finais ({len(confirmed_patterns)} confirmados)...',
                'total_trades': len(confirmed_patterns),
                'current_timestamp': last_timestamp
            })
            
        self.signals = []
        for pattern in confirmed_patterns:
            # Verifica se não geramos sinal num intervalo recente
            if not self.signals:
                self.signals.append({
                    'timestamp': pattern['breakout_timestamp'],
                    'price': self.df.loc[pattern['breakout_timestamp'], 'close'],
                    'direction': 'long',
                    'strength': pattern['strength'],
                    'metadata': {
                        'trend': pattern['metadata']['trend'],
                        'first_bottom': pattern['first_bottom'],
                        'second_bottom': pattern['second_bottom'],
                        'neckline': pattern.get('neckline', None),
                        'rsi_divergence': pattern['metadata']['rsi_divergence'],
                        'volume_ratio': pattern['metadata']['volume_ratio'],
                        'breakout_volume': pattern['metadata']['breakout_volume'],
                        'risk_reward': pattern['metadata']['risk_reward'],
                        'stop_loss_pct': pattern['metadata']['stop_loss_pct']
                    }
                })
            else:
                # Verificar se deve gerar novo sinal baseado no intervalo mínimo
                if self._should_generate_signal(pattern['breakout_timestamp']):
                    self.signals.append({
                        'timestamp': pattern['breakout_timestamp'],
                        'price': self.df.loc[pattern['breakout_timestamp'], 'close'],
                        'direction': 'long',
                        'strength': pattern['strength'],
                        'metadata': pattern['metadata']
                    })
        
        # Final progress update
        if progress_callback:
            last_timestamp = self.df.iloc[-1]['timestamp']
            progress_callback(100, last_timestamp, {
                'message': f'Análise concluída. {len(self.signals)} sinais gerados.',
                'total_trades': len(self.signals),
                'current_timestamp': last_timestamp
            })
        
        return self.signals
