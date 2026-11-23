# eva.py - Módulo de Análisis de Valor Ganado (Earned Value Analysis)
import pandas as pd
import numpy as np

def calculate_evm(tasks_df, status_date=None):
    """
    Calcula métricas de Earned Value Management (EVM) para el proyecto.
    
    Args:
        tasks_df: DataFrame con las tareas del proyecto
        status_date: Fecha de estado para el cálculo (default: fecha actual)
    
    Returns:
        DataFrame con métricas EVA por tarea
    """
    if tasks_df.empty:
        return pd.DataFrame()
    
    # Configurar fecha de estado
    status_date = status_date or pd.Timestamp.today()
    
    # Calcular métricas básicas
    tasks_df['BAC'] = tasks_df['Cost']  # Budget at Completion
    
    # Función para calcular PV (Planned Value)
    def calcular_pv(row):
        if pd.isna(row['Start']) or pd.isna(row['Finish']) or row['Start'] > row['Finish']:
            return 0.0 # No hay fechas válidas, PV es 0
        
        # Si la tarea ya ha terminado en la fecha de estado, el PV es el BAC completo
        if status_date >= row['Finish']:
            return row['BAC']
        
        # Si la tarea aún no ha comenzado en la fecha de estado, el PV es 0
        if status_date < row['Start']:
            return 0.0
        
        # Calcular la duración total de la tarea
        total_duration_days = (row['Finish'] - row['Start']).days + 1
        
        # Calcular los días planificados hasta la fecha de estado
        planned_days_until_status = (status_date - row['Start']).days + 1
        
        # Asegurarse de que no haya división por cero y que el progreso no exceda el 100%
        if total_duration_days <= 0:
            return row['BAC'] if status_date >= row['Start'] else 0.0
        
        progress_ratio = min(1.0, max(0.0, planned_days_until_status / total_duration_days))
        return row['BAC'] * progress_ratio
            
    tasks_df['PV'] = tasks_df.apply(calcular_pv, axis=1)
    tasks_df['EV'] = tasks_df['BAC'] * tasks_df['Progress'] / 100
    tasks_df['AC'] = tasks_df['Actual_Cost'].fillna(tasks_df['EV'])  # Si no hay costo real, usar EV como aproximación
    
    # Calcular variaciones e índices
    tasks_df['CV'] = tasks_df['EV'] - tasks_df['AC']  # Cost Variance
    tasks_df['SV'] = tasks_df['EV'] - tasks_df['PV']  # Schedule Variance
    
    # Calcular índices evitando división por cero
    tasks_df['CPI'] = tasks_df.apply(lambda x: x['EV'] / x['AC'] if x['AC'] > 0 else 1, axis=1)
    tasks_df['SPI'] = tasks_df.apply(lambda x: x['EV'] / x['PV'] if x['PV'] > 0 else 1, axis=1)
    
    # Manejar valores infinitos y NaN
    tasks_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    tasks_df.fillna(0, inplace=True)
    
    # Calcular estimaciones
    tasks_df['ETC'] = (tasks_df['BAC'] - tasks_df['EV']) / tasks_df['CPI']  # Estimate to Complete
    tasks_df['EAC'] = tasks_df['AC'] + tasks_df['ETC']  # Estimate at Completion
    tasks_df['VAC'] = tasks_df['BAC'] - tasks_df['EAC']  # Variance at Completion
    
    # Manejar nuevamente posibles divisiones por cero en estimaciones
    tasks_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    tasks_df.fillna(0, inplace=True)
    
    return tasks_df[['TaskID', 'Task', 'BAC', 'PV', 'EV', 'AC', 'CV', 'SV', 'CPI', 'SPI', 'ETC', 'EAC', 'VAC']]

def calculate_project_evm(evm_df):
    """Calcula las métricas EVA a nivel de proyecto"""
    if evm_df.empty:
        return {}
    
    return {
        'BAC': evm_df['BAC'].sum(),
        'PV': evm_df['PV'].sum(),
        'EV': evm_df['EV'].sum(),
        'AC': evm_df['AC'].sum(),
        'CV': evm_df['CV'].sum(),
        'SV': evm_df['SV'].sum(),
        'CPI': evm_df['EV'].sum() / evm_df['AC'].sum() if evm_df['AC'].sum() > 0 else 0,
        'SPI': evm_df['EV'].sum() / evm_df['PV'].sum() if evm_df['PV'].sum() > 0 else 0,
        'EAC': evm_df['EAC'].sum(),
        'VAC': evm_df['VAC'].sum()
    }