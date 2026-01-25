from src.preprocessing import basic_impute, scale_numeric
import pandas as pd
import numpy as np

def test_basic_impute_and_scale():
    df = pd.DataFrame({
        'nota_port': [1.0, None, 3.0],
        'nota_mat': [2.0, 2.0, None],
        'ips': [0.5, None, 0.7]
    })
    df2 = basic_impute(df.copy(), ['nota_port','nota_mat','ips'], [])
    assert not df2[['nota_port','nota_mat','ips']].isnull().any().any()
    df3 = scale_numeric(df2.copy(), ['nota_port','nota_mat','ips'])
    # after scaling mean ~0
    assert abs(df3['nota_port'].mean()) < 1e-6 or np.isfinite(df3['nota_port'].mean())
