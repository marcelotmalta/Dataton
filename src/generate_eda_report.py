
import pandas as pd
import os

# Configuration
DATA_PATH = r'data\BASE DE DADOS PEDE 2024 - DATATHON.xlsx'
REPORT_PATH = r'docs\EDA_REPORT.md'

def generate_report():
    print("Loading data...")
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    df = pd.read_excel(DATA_PATH)
    
    # 1. Pipeline de Limpeza (Cópia do Notebook)
    cols_interest = [
        'Defas',  
        'INDE 22', 'IPS', 'IEG', 'IDA', 'IPV', 'IAA', 'IAN',
        'Fase', 'Turma', 'Ano ingresso', 'Instituição de ensino', 'Pedra 22'
    ]
    
    # Filtrar
    cols_to_keep = [c for c in cols_interest if c in df.columns]
    df = df[cols_to_keep].copy()
    
    # Padronizar
    df.columns = [c.strip().upper().replace(' ', '_') for c in df.columns]
    
    # Start Markdown Builder
    md_lines = []
    md_lines.append("# Relatório de Análise Exploratória de Dados (EDA)")
    md_lines.append(f"\n**Data de Geração**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    md_lines.append(f"\n**Total de Registros**: {df.shape[0]}")
    md_lines.append(f"**Total de Colunas**: {df.shape[1]}")
    
    # 2. Tipos de Dados
    md_lines.append("\n## 1. Tipos de Dados")
    md_lines.append("| Coluna | Tipo |")
    md_lines.append("| --- | --- |")
    for col, dtype in df.dtypes.items():
        md_lines.append(f"| {col} | {dtype} |")
        
    # 3. Missing Values
    md_lines.append("\n## 2. Valores Ausentes (Missingness)")
    missing = df.isnull().sum()
    missing_pct = (df.isnull().mean() * 100).round(2)
    missing_df = pd.DataFrame({'Missing': missing, '%': missing_pct})
    missing_df = missing_df[missing_df['Missing'] > 0].sort_values('%', ascending=False)
    
    if missing_df.empty:
        md_lines.append("\nNão há valores ausentes no dataset filtrado.")
    else:
        md_lines.append("| Coluna | Qtd Missing | % Missing |")
        md_lines.append("| --- | --- | --- |")
        for col, row in missing_df.iterrows():
            md_lines.append(f"| {col} | {row['Missing']} | {row['%']}% |")

    # 4. Distribuições Numéricas
    md_lines.append("\n## 3. Estatísticas Descritivas (Numéricas)")
    num_df = df.select_dtypes(include=['float64', 'int64'])
    if not num_df.empty:
        desc = num_df.describe().T.round(2)
        # Convert to markdown table manually or use to_markdown if available (pandas 1.0+)
        # Header
        md_lines.append("| Coluna | Count | Mean | Std | Min | 25% | 50% | 75% | Max |")
        md_lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for col, row in desc.iterrows():
            md_lines.append(f"| {col} | {row['count']} | {row['mean']} | {row['std']} | {row['min']} | {row['25%']} | {row['50%']} | {row['75%']} | {row['max']} |")
    else:
        md_lines.append("\nNenhuma coluna numérica encontrada.")

    # 5. Target Distribution
    md_lines.append("\n## 4. Distribuição do Target (DEFAS)")
    if 'DEFAS' in df.columns:
        vc = df['DEFAS'].value_counts()
        vc_pct = (df['DEFAS'].value_counts(normalize=True) * 100).round(2)
        md_lines.append("| Categoria | Contagem | % |")
        md_lines.append("| --- | --- | --- |")
        for cat in vc.index:
            md_lines.append(f"| {cat} | {vc[cat]} | {vc_pct[cat]}% |")
    else:
        md_lines.append("\nTarget 'DEFAS' não encontrado.")

    # 6. Correlações
    md_lines.append("\n## 5. Correlações (Pearson)")
    if num_df.shape[1] > 1:
        corr_matrix = num_df.corr().round(2)
        # Let's list strong correlations (> 0.5 or < -0.5) distinct from 1.0
        strong_corrs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i):
                val = corr_matrix.iloc[i, j]
                if abs(val) >= 0.5:
                    c1 = corr_matrix.columns[i]
                    c2 = corr_matrix.columns[j]
                    strong_corrs.append((c1, c2, val))
        
        strong_corrs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        if strong_corrs:
            md_lines.append("| Variável 1 | Variável 2 | Correlação |")
            md_lines.append("| --- | --- | --- |")
            for c1, c2, val in strong_corrs:
                md_lines.append(f"| {c1} | {c2} | {val} |")
        else:
            md_lines.append("\nNenhuma correlação forte (> 0.5) detectada.")
    else:
        md_lines.append("\nDados insuficientes para correlação.")

    # Write to File
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    print(f"Report successfully generated at: {REPORT_PATH}")

if __name__ == "__main__":
    generate_report()
